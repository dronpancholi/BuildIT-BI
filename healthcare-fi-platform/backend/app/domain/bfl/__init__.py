"""
BuildIT Formula Language (BFL)
==============================
Complete expression language for healthcare financial calculations.
Supports arithmetic, aggregation, time intelligence, conditionals,
and generates SQL for PostgreSQL, Snowflake, and BigQuery.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4


# ─────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────

class FormulaNodeType(Enum):
    LITERAL_NUMBER = "literal_number"
    LITERAL_STRING = "literal_string"
    IDENTIFIER = "identifier"
    BINARY_OP = "binary_op"
    UNARY_OP = "unary_op"
    FUNCTION_CALL = "function_call"
    AGGREGATION = "aggregation"
    TIME_INTELLIGENCE = "time_intelligence"
    CONDITIONAL = "conditional"
    COMPARISON = "comparison"


class SQLDialect(Enum):
    POSTGRESQL = "postgresql"
    SNOWFLAKE = "snowflake"
    BIGQUERY = "bigquery"


class FormulaStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class AggregationType(Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    MIN = "min"
    MAX = "max"
    FIRST = "first"
    LAST = "last"
    MEDIAN = "median"
    STDDEV = "stddev"


# ─────────────────────────────────────────────
# AST Node
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class SourceSpan:
    line: int
    column: int
    length: int


@dataclass(frozen=True)
class FormulaExpression:
    node_type: FormulaNodeType
    value: Any
    children: tuple[FormulaExpression, ...] = field(default_factory=tuple)
    source_span: Optional[SourceSpan] = None


# ─────────────────────────────────────────────
# Error types
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class FormulaError:
    code: str
    message: str
    span: Optional[SourceSpan] = None


# ─────────────────────────────────────────────
# Formula entity
# ─────────────────────────────────────────────

@dataclass
class Formula:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    expression_text: str = ""
    ast: Optional[FormulaExpression] = None
    status: FormulaStatus = FormulaStatus.DRAFT
    version: int = 1
    created_by: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None

    def publish(self) -> None:
        self.status = FormulaStatus.PUBLISHED
        self.published_at = datetime.utcnow()

    def deprecate(self) -> None:
        self.status = FormulaStatus.DEPRECATED
        self.deprecated_at = datetime.utcnow()

    def archive(self) -> None:
        self.status = FormulaStatus.ARCHIVED


# ─────────────────────────────────────────────
# Token types for Lexer
# ─────────────────────────────────────────────

class TokenType(Enum):
    NUMBER = "NUMBER"
    STRING = "STRING"
    IDENT = "IDENT"
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    PERCENT = "PERCENT"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    EQ = "EQ"
    NEQ = "NEQ"
    LT = "LT"
    GT = "GT"
    LTE = "LTE"
    GTE = "GTE"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    IF = "IF"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    span: SourceSpan


# ─────────────────────────────────────────────
# Lexer
# ─────────────────────────────────────────────

class FormulaLexer:
    """Tokenize BFL expression text into a list of tokens."""

    KEYWORDS: dict[str, TokenType] = {
        "AND": TokenType.AND,
        "OR": TokenType.OR,
        "NOT": TokenType.NOT,
        "IF": TokenType.IF,
    }

    def tokenize(self, text: str) -> list[Token]:
        tokens: list[Token] = []
        i = 0
        line = 1
        col = 1

        while i < len(text):
            ch = text[i]

            # whitespace
            if ch in (" ", "\t", "\r"):
                i += 1
                col += 1
                continue
            if ch == "\n":
                i += 1
                line += 1
                col = 1
                continue

            # skip line comments
            if ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
                while i < len(text) and text[i] != "\n":
                    i += 1
                continue

            # numbers: optional leading minus handled as MINUS token in parser
            if ch.isdigit() or (ch == "." and i + 1 < len(text) and text[i + 1].isdigit()):
                start_col = col
                num_str = ""
                has_dot = False
                while i < len(text) and (text[i].isdigit() or text[i] == "."):
                    if text[i] == ".":
                        if has_dot:
                            break
                        has_dot = True
                    num_str += text[i]
                    i += 1
                    col += 1
                tokens.append(Token(TokenType.NUMBER, num_str, SourceSpan(line, start_col, len(num_str))))
                continue

            # strings
            if ch in ("'", '"'):
                quote = ch
                start_col = col
                i += 1
                col += 1
                s = ""
                while i < len(text) and text[i] != quote:
                    if text[i] == "\\":
                        i += 1
                        col += 1
                        if i < len(text):
                            s += text[i]
                            i += 1
                            col += 1
                    else:
                        s += text[i]
                        i += 1
                        col += 1
                if i < len(text):
                    i += 1
                    col += 1
                tokens.append(Token(TokenType.STRING, s, SourceSpan(line, start_col, len(s) + 2)))
                continue

            # identifiers / keywords
            if ch.isalpha() or ch == "_":
                start_col = col
                ident = ""
                while i < len(text) and (text[i].isalnum() or text[i] == "_"):
                    ident += text[i]
                    i += 1
                    col += 1
                upper = ident.upper()
                if upper in self.KEYWORDS:
                    tokens.append(Token(self.KEYWORDS[upper], upper, SourceSpan(line, start_col, len(ident))))
                else:
                    tokens.append(Token(TokenType.IDENT, ident, SourceSpan(line, start_col, len(ident))))
                continue

            # two-char operators
            if ch == "!" and i + 1 < len(text) and text[i + 1] == "=":
                tokens.append(Token(TokenType.NEQ, "!=", SourceSpan(line, col, 2)))
                i += 2
                col += 2
                continue
            if ch == "<" and i + 1 < len(text) and text[i + 1] == "=":
                tokens.append(Token(TokenType.LTE, "<=", SourceSpan(line, col, 2)))
                i += 2
                col += 2
                continue
            if ch == ">" and i + 1 < len(text) and text[i + 1] == "=":
                tokens.append(Token(TokenType.GTE, ">=", SourceSpan(line, col, 2)))
                i += 2
                col += 2
                continue

            # single-char operators
            op_map = {
                "+": TokenType.PLUS,
                "-": TokenType.MINUS,
                "*": TokenType.STAR,
                "/": TokenType.SLASH,
                "%": TokenType.PERCENT,
                "(": TokenType.LPAREN,
                ")": TokenType.RPAREN,
                ",": TokenType.COMMA,
                "=": TokenType.EQ,
                "<": TokenType.LT,
                ">": TokenType.GT,
            }
            if ch in op_map:
                tokens.append(Token(op_map[ch], ch, SourceSpan(line, col, 1)))
                i += 1
                col += 1
                continue

            # unknown character – skip
            i += 1
            col += 1

        tokens.append(Token(TokenType.EOF, "", SourceSpan(line, col, 0)))
        return tokens


# ─────────────────────────────────────────────
# Parser  (recursive-descent)
# ─────────────────────────────────────────────
#
# Precedence  (lowest → highest):
#   OR
#   AND
#   comparison   =  !=  <  >  <=  >=
#   additive     +  -
#   multiplicative  *  /  %
#   unary        NOT  -
#   primary      NUMBER | STRING | IDENT | function_call
#                | aggregation | time_intel | ( expr )

class FormulaParser:
    """Parse a token list into an AST (FormulaExpression)."""

    def __init__(self) -> None:
        self._tokens: list[Token] = []
        self._pos: int = 0

    # ── helpers ──────────────────────────────
    def _current(self) -> Token:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else Token(TokenType.EOF, "", SourceSpan(0, 0, 0))

    def _peek(self) -> Token:
        return self._current()

    def _advance(self) -> Token:
        tok = self._current()
        if self._pos < len(self._tokens):
            self._pos += 1
        return tok

    def _expect(self, tt: TokenType) -> Token:
        tok = self._current()
        if tok.type != tt:
            raise SyntaxError(
                f"Expected {tt.value} but got {tok.type.value} '{tok.value}' "
                f"at line {tok.span.line}, col {tok.span.column}"
            )
        return self._advance()

    def _match(self, *types: TokenType) -> Optional[Token]:
        if self._current().type in types:
            return self._advance()
        return None

    # ── grammar ──────────────────────────────
    def parse(self, tokens: list[Token]) -> FormulaExpression:
        self._tokens = tokens
        self._pos = 0
        expr = self._or_expr()
        return expr

    def _or_expr(self) -> FormulaExpression:
        left = self._and_expr()
        while self._match(TokenType.OR):
            right = self._and_expr()
            left = FormulaExpression(
                node_type=FormulaNodeType.BINARY_OP,
                value="OR",
                children=(left, right),
            )
        return left

    def _and_expr(self) -> FormulaExpression:
        left = self._comparison()
        while self._match(TokenType.AND):
            right = self._comparison()
            left = FormulaExpression(
                node_type=FormulaNodeType.BINARY_OP,
                value="AND",
                children=(left, right),
            )
        return left

    def _comparison(self) -> FormulaExpression:
        left = self._additive()
        while True:
            tok = self._current()
            if tok.type in (TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
                op = self._advance()
                right = self._additive()
                left = FormulaExpression(
                    node_type=FormulaNodeType.COMPARISON,
                    value=op.value,
                    children=(left, right),
                )
            else:
                break
        return left

    def _additive(self) -> FormulaExpression:
        left = self._multiplicative()
        while self._current().type in (TokenType.PLUS, TokenType.MINUS):
            op = self._advance()
            right = self._multiplicative()
            left = FormulaExpression(
                node_type=FormulaNodeType.BINARY_OP,
                value=op.value,
                children=(left, right),
            )
        return left

    def _multiplicative(self) -> FormulaExpression:
        left = self._unary()
        while self._current().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._advance()
            right = self._unary()
            left = FormulaExpression(
                node_type=FormulaNodeType.BINARY_OP,
                value=op.value,
                children=(left, right),
            )
        return left

    def _unary(self) -> FormulaExpression:
        if self._match(TokenType.NOT):
            operand = self._unary()
            return FormulaExpression(
                node_type=FormulaNodeType.UNARY_OP,
                value="NOT",
                children=(operand,),
            )
        if self._match(TokenType.MINUS):
            operand = self._unary()
            return FormulaExpression(
                node_type=FormulaNodeType.UNARY_OP,
                value="-",
                children=(operand,),
            )
        return self._primary()

    def _primary(self) -> FormulaExpression:
        tok = self._current()

        # parenthesised sub-expression
        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._or_expr()
            self._expect(TokenType.RPAREN)
            return expr

        # number literal
        if tok.type == TokenType.NUMBER:
            self._advance()
            return FormulaExpression(
                node_type=FormulaNodeType.LITERAL_NUMBER,
                value=tok.value,
                source_span=tok.span,
            )

        # string literal
        if tok.type == TokenType.STRING:
            self._advance()
            return FormulaExpression(
                node_type=FormulaNodeType.LITERAL_STRING,
                value=tok.value,
                source_span=tok.span,
            )

        # identifier – could be variable, aggregation, time-intel, or function
        # Also handle keyword tokens that can be function calls (IF, AND, OR, NOT)
        if tok.type in (TokenType.IDENT, TokenType.IF, TokenType.AND, TokenType.OR, TokenType.NOT):
            name = tok.value
            upper = name.upper()
            self._advance()

            # check for function call  NAME(args)
            if self._current().type == TokenType.LPAREN:
                self._advance()  # consume (
                args: list[FormulaExpression] = []
                if self._current().type != TokenType.RPAREN:
                    args.append(self._or_expr())
                    while self._match(TokenType.COMMA):
                        args.append(self._or_expr())
                self._expect(TokenType.RPAREN)
                children = tuple(args)

                # classify
                if upper in _AGGREGATION_NAMES:
                    return FormulaExpression(
                        node_type=FormulaNodeType.AGGREGATION,
                        value=upper,
                        children=children,
                        source_span=tok.span,
                    )
                if upper in _TIME_INTEL_NAMES:
                    return FormulaExpression(
                        node_type=FormulaNodeType.TIME_INTELLIGENCE,
                        value=upper,
                        children=children,
                        source_span=tok.span,
                    )
                # IF is always conditional
                if upper == "IF":
                    return FormulaExpression(
                        node_type=FormulaNodeType.CONDITIONAL,
                        value=upper,
                        children=children,
                        source_span=tok.span,
                    )
                return FormulaExpression(
                    node_type=FormulaNodeType.FUNCTION_CALL,
                    value=name,
                    children=children,
                    source_span=tok.span,
                )

            # plain identifier / metric reference
            return FormulaExpression(
                node_type=FormulaNodeType.IDENTIFIER,
                value=name,
                source_span=tok.span,
            )

        raise SyntaxError(
            f"Unexpected token {tok.type.value} '{tok.value}' "
            f"at line {tok.span.line}, col {tok.span.column}"
        )


# ─────────────────────────────────────────────
# Semantic Analyzer
# ─────────────────────────────────────────────

class FormulaSemanticAnalyzer:
    """Validate an AST: function names exist, arg counts match, etc."""

    def analyze(
        self,
        ast: FormulaExpression,
        known_metrics: Optional[dict[str, str]] = None,
    ) -> list[FormulaError]:
        errors: list[FormulaError] = []
        known_metrics = known_metrics or {}
        self._walk(ast, errors, known_metrics)
        return errors

    def _walk(
        self,
        node: FormulaExpression,
        errors: list[FormulaError],
        known: dict[str, str],
    ) -> None:
        if node.node_type == FormulaNodeType.IDENTIFIER:
            name = node.value.upper()
            if name not in known and name not in FunctionRegistry.all_names():
                errors.append(FormulaError(
                    "UNKNOWN_METRIC",
                    f"Unknown metric '{node.value}'",
                    node.source_span,
                ))

        elif node.node_type in (
            FormulaNodeType.FUNCTION_CALL,
            FormulaNodeType.AGGREGATION,
            FormulaNodeType.TIME_INTELLIGENCE,
            FormulaNodeType.CONDITIONAL,
        ):
            name = node.value.upper()
            meta = FunctionRegistry.get(name)
            if meta is None:
                errors.append(FormulaError(
                    "UNKNOWN_FUNCTION",
                    f"Unknown function '{node.value}'",
                    node.source_span,
                ))
            else:
                expected = meta["args"]
                actual = len(node.children)
                if expected >= 0 and actual != expected:
                    errors.append(FormulaError(
                        "WRONG_ARG_COUNT",
                        f"Function '{node.value}' expects {expected} args, got {actual}",
                        node.source_span,
                    ))

        elif node.node_type == FormulaNodeType.BINARY_OP:
            if node.value in ("*", "/", "%") and len(node.children) == 2:
                right = node.children[1]
                if right.node_type == FormulaNodeType.LITERAL_NUMBER and right.value == "0":
                    errors.append(FormulaError(
                        "DIVISION_BY_ZERO",
                        "Division by zero detected",
                        node.source_span,
                    ))

        for child in node.children:
            self._walk(child, errors, known)


# ─────────────────────────────────────────────
# SQL Generator
# ─────────────────────────────────────────────

class FormulaSQLGenerator:
    """Generate SQL from an AST for a given dialect."""

    def generate(
        self,
        ast: FormulaExpression,
        dialect: SQLDialect = SQLDialect.POSTGRESQL,
        metric_table: str = "metrics",
        date_column: str = "transaction_date",
    ) -> str:
        return self._emit(ast, dialect, metric_table, date_column)

    # ── dialect helpers ──────────────────────
    @staticmethod
    def _date_trunc(granularity: str, col: str, dialect: SQLDialect) -> str:
        if dialect == SQLDialect.BIGQUERY:
            return f"DATE_TRUNC({col}, {granularity})"
        return f"DATE_TRUNC('{granularity}', {col})"

    @staticmethod
    def _current_date(dialect: SQLDialect) -> str:
        if dialect == SQLDialect.SNOWFLAKE:
            return "CURRENT_DATE()"
        if dialect == SQLDialect.BIGQUERY:
            return "CURRENT_DATE()"
        return "CURRENT_DATE"

    @staticmethod
    def _interval(value: str, unit: str, dialect: SQLDialect) -> str:
        if dialect == SQLDialect.BIGQUERY:
            return f"DATE_SUB({FormulaSQLGenerator._current_date(dialect)}, INTERVAL {value} {unit})"
        if dialect == SQLDialect.SNOWFLAKE:
            return f"DATEADD({unit}, -{value}, CURRENT_DATE())"
        return f"CURRENT_DATE - INTERVAL '{value} {unit}'"

    def _metric_expr(self, metric_name: str, metric_table: str) -> str:
        return (
            f"SUM(CASE WHEN {metric_table}.metric_name = '{metric_name}' "
            f"THEN {metric_table}.value END)"
        )

    def _date_filter(self, date_column: str, op: str, bound: str) -> str:
        return f"{date_column} {op} {bound}"

    # ── main recursive emitter ───────────────
    def _emit(
        self,
        node: FormulaExpression,
        dialect: SQLDialect,
        metric_table: str,
        date_column: str,
    ) -> str:
        # ── literals ─────────────────────────
        if node.node_type == FormulaNodeType.LITERAL_NUMBER:
            return str(node.value)
        if node.node_type == FormulaNodeType.LITERAL_STRING:
            return f"'{node.value}'"

        # ── identifier (metric reference) ────
        if node.node_type == FormulaNodeType.IDENTIFIER:
            return self._metric_expr(node.value, metric_table)

        # ── binary op ────────────────────────
        if node.node_type == FormulaNodeType.BINARY_OP:
            left = self._emit(node.children[0], dialect, metric_table, date_column)
            right = self._emit(node.children[1], dialect, metric_table, date_column)
            op = node.value
            if op == "AND":
                return f"({left} AND {right})"
            if op == "OR":
                return f"({left} OR {right})"
            return f"({left} {op} {right})"

        # ── unary op ─────────────────────────
        if node.node_type == FormulaNodeType.UNARY_OP:
            operand = self._emit(node.children[0], dialect, metric_table, date_column)
            if node.value == "NOT":
                return f"(NOT {operand})"
            return f"(-{operand})"

        # ── comparison ────────────────────────
        if node.node_type == FormulaNodeType.COMPARISON:
            left = self._emit(node.children[0], dialect, metric_table, date_column)
            right = self._emit(node.children[1], dialect, metric_table, date_column)
            return f"({left} {node.value} {right})"

        # ── function call ─────────────────────
        if node.node_type == FormulaNodeType.FUNCTION_CALL:
            args_sql = [
                self._emit(a, dialect, metric_table, date_column)
                for a in node.children
            ]
            return f"{node.value}({', '.join(args_sql)})"

        # ── conditional ───────────────────────
        if node.node_type == FormulaNodeType.CONDITIONAL:
            return self._emit_conditional(node, dialect, metric_table, date_column)

        # ── aggregation ───────────────────────
        if node.node_type == FormulaNodeType.AGGREGATION:
            return self._emit_aggregation(node, dialect, metric_table, date_column)

        # ── time intelligence ─────────────────
        if node.node_type == FormulaNodeType.TIME_INTELLIGENCE:
            return self._emit_time_intel(node, dialect, metric_table, date_column)

        return "/* unknown node */"

    # ── aggregation ──────────────────────────
    def _emit_aggregation(
        self,
        node: FormulaExpression,
        dialect: SQLDialect,
        metric_table: str,
        date_column: str,
    ) -> str:
        fn = node.value.upper()
        inner = self._emit(node.children[0], dialect, metric_table, date_column)
        if fn == "SUM":
            return f"SUM({inner})"
        if fn == "AVG":
            return f"AVG({inner})"
        if fn == "COUNT":
            return f"COUNT({inner})"
        if fn == "COUNT_DISTINCT":
            return f"COUNT(DISTINCT {inner})"
        if fn == "MIN":
            return f"MIN({inner})"
        if fn == "MAX":
            return f"MAX({inner})"
        if fn == "MEDIAN":
            if dialect == SQLDialect.POSTGRESQL:
                return f"PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {inner})"
            if dialect == SQLDialect.SNOWFLAKE:
                return f"MEDIAN({inner})"
            return f"APPROX_QUANTILES({inner}, 2)[OFFSET(1)]"
        if fn == "STDDEV":
            return f"STDDEV({inner})"
        if fn == "FIRST":
            if dialect == SQLDialect.POSTGRESQL:
                return f"(ARRAY_AGG({inner} ORDER BY {date_column} ASC))[1]"
            return f"FIRST_VALUE({inner})"
        if fn == "LAST":
            if dialect == SQLDialect.POSTGRESQL:
                return f"(ARRAY_AGG({inner} ORDER BY {date_column} DESC))[1]"
            return f"LAST_VALUE({inner})"
        return f"{fn}({inner})"

    # ── time intelligence ────────────────────
    def _emit_time_intel(
        self,
        node: FormulaExpression,
        dialect: SQLDialect,
        metric_table: str,
        date_column: str,
    ) -> str:
        fn = node.value.upper()
        metric_sql = self._metric_expr(node.children[0].value, metric_table) if node.children else "0"
        cd = self._current_date(dialect)
        dt = self._date_trunc

        if fn == "YTD":
            start = dt("year", date_column, dialect)
            return f"SUM(CASE WHEN {date_column} >= {start} AND {date_column} <= {cd} THEN {metric_table}.value END)"
        if fn == "MTD":
            start = dt("month", date_column, dialect)
            return f"SUM(CASE WHEN {date_column} >= {start} AND {date_column} <= {cd} THEN {metric_table}.value END)"
        if fn == "QTD":
            start = dt("quarter", date_column, dialect)
            return f"SUM(CASE WHEN {date_column} >= {start} AND {date_column} <= {cd} THEN {metric_table}.value END)"
        if fn == "PY":
            prev = self._interval("1", "year", dialect)
            return (
                f"SUM(CASE WHEN {date_column} >= {dt('year', prev, dialect)} "
                f"AND {date_column} <= {prev} THEN {metric_table}.value END)"
            )
        if fn == "PM":
            prev = self._interval("1", "month", dialect)
            return (
                f"SUM(CASE WHEN {date_column} >= {dt('month', prev, dialect)} "
                f"AND {date_column} <= {prev} THEN {metric_table}.value END)"
            )
        if fn == "PQ":
            prev = self._interval("1", "quarter", dialect)
            return (
                f"SUM(CASE WHEN {date_column} >= {dt('quarter', prev, dialect)} "
                f"AND {date_column} <= {prev} THEN {metric_table}.value END)"
            )
        if fn == "YOY":
            return f"({metric_sql} - {self._emit(FormulaExpression(FormulaNodeType.TIME_INTELLIGENCE, 'PY', node.children), dialect, metric_table, date_column)})"
        if fn == "MOM":
            return f"({metric_sql} - {self._emit(FormulaExpression(FormulaNodeType.TIME_INTELLIGENCE, 'PM', node.children), dialect, metric_table, date_column)})"
        if fn == "QOQ":
            return f"({metric_sql} - {self._emit(FormulaExpression(FormulaNodeType.TIME_INTELLIGENCE, 'PQ', node.children), dialect, metric_table, date_column)})"
        if fn == "ROLLING3":
            return (
                f"SUM(CASE WHEN {date_column} >= {self._interval('3', 'month', dialect)} "
                f"AND {date_column} <= {cd} THEN {metric_table}.value END)"
            )
        if fn == "ROLLING6":
            return (
                f"SUM(CASE WHEN {date_column} >= {self._interval('6', 'month', dialect)} "
                f"AND {date_column} <= {cd} THEN {metric_table}.value END)"
            )
        if fn == "ROLLING12":
            return (
                f"SUM(CASE WHEN {date_column} >= {self._interval('12', 'month', dialect)} "
                f"AND {date_column} <= {cd} THEN {metric_table}.value END)"
            )
        if fn == "RUNNING_SUM":
            return (
                f"SUM({metric_sql}) OVER (ORDER BY {date_column} ROWS UNBOUNDED PRECEDING)"
            )
        if fn == "RUNNING_AVG":
            return (
                f"AVG({metric_sql}) OVER (ORDER BY {date_column} ROWS UNBOUNDED PRECEDING)"
            )
        if fn == "RANK":
            return f"RANK() OVER (ORDER BY {metric_sql} DESC)"
        if fn == "RANKDENSE":
            return f"DENSE_RANK() OVER (ORDER BY {metric_sql} DESC)"
        if fn == "PCTOF":
            other = self._metric_expr(node.children[1].value, metric_table) if len(node.children) > 1 else "1"
            return f"CASE WHEN {other} = 0 THEN 0 ELSE {metric_sql} / {other} END"
        if fn == "PCTCHANGE":
            other = self._metric_expr(node.children[1].value, metric_table) if len(node.children) > 1 else "0"
            return f"CASE WHEN {other} = 0 THEN 0 ELSE ({metric_sql} - {other}) / {other} END"
        if fn == "BUDGETVARIANCE":
            budget = self._metric_expr(node.children[1].value, metric_table) if len(node.children) > 1 else "0"
            return f"({metric_sql} - {budget})"
        if fn == "BUDGETPCTVARIANCE":
            budget = self._metric_expr(node.children[1].value, metric_table) if len(node.children) > 1 else "1"
            return f"CASE WHEN {budget} = 0 THEN 0 ELSE ({metric_sql} - {budget}) / {budget} END"
        if fn == "FORECASTVARIANCE":
            forecast = self._metric_expr(node.children[1].value, metric_table) if len(node.children) > 1 else "0"
            return f"({metric_sql} - {forecast})"
        return f"/* {fn} */"

    # ── conditional ──────────────────────────
    def _emit_conditional(
        self,
        node: FormulaExpression,
        dialect: SQLDialect,
        metric_table: str,
        date_column: str,
    ) -> str:
        fn = node.value.upper()
        if fn == "IF":
            cond = self._emit(node.children[0], dialect, metric_table, date_column)
            t_val = self._emit(node.children[1], dialect, metric_table, date_column)
            f_val = self._emit(node.children[2], dialect, metric_table, date_column)
            return f"CASE WHEN {cond} THEN {t_val} ELSE {f_val} END"

        if fn == "IFS":
            parts: list[str] = []
            for i in range(0, len(node.children) - 1, 2):
                c = self._emit(node.children[i], dialect, metric_table, date_column)
                v = self._emit(node.children[i + 1], dialect, metric_table, date_column)
                parts.append(f"WHEN {c} THEN {v}")
            if len(node.children) % 2 == 1:
                default = self._emit(node.children[-1], dialect, metric_table, date_column)
                parts.append(f"ELSE {default}")
            return "CASE " + " ".join(parts) + " END"

        if fn == "SWITCH":
            expr = self._emit(node.children[0], dialect, metric_table, date_column)
            parts = []
            for i in range(1, len(node.children) - 1, 2):
                val = self._emit(node.children[i], dialect, metric_table, date_column)
                res = self._emit(node.children[i + 1], dialect, metric_table, date_column)
                parts.append(f"WHEN {expr} = {val} THEN {res}")
            if len(node.children) % 2 == 0:
                default = self._emit(node.children[-1], dialect, metric_table, date_column)
                parts.append(f"ELSE {default}")
            return "CASE " + " ".join(parts) + " END"

        if fn == "ISBLANK":
            inner = self._emit(node.children[0], dialect, metric_table, date_column)
            return f"({inner} IS NULL)"
        if fn == "ISERROR":
            inner = self._emit(node.children[0], dialect, metric_table, date_column)
            return f"({inner} IS NULL)"
        if fn == "IFERROR":
            inner = self._emit(node.children[0], dialect, metric_table, date_column)
            fallback = self._emit(node.children[1], dialect, metric_table, date_column)
            return f"CASE WHEN {inner} IS NULL THEN {fallback} ELSE {inner} END"

        return "/* unknown conditional */"


# ─────────────────────────────────────────────
# Function Registry
# ─────────────────────────────────────────────

# Helper sets used by parser to classify identifiers
_AGGREGATION_NAMES: set[str] = {
    "SUM", "AVG", "COUNT", "COUNT_DISTINCT", "MIN", "MAX",
    "FIRST", "LAST", "MEDIAN", "STDDEV",
}
_TIME_INTEL_NAMES: set[str] = {
    "YTD", "MTD", "QTD", "PY", "PM", "PQ",
    "YOY", "MOM", "QOQ", "ROLLING3", "ROLLING6", "ROLLING12",
    "RUNNING_SUM", "RUNNING_AVG", "RANK", "RANKDENSE",
    "PCTOF", "PCTCHANGE",
    "BUDGETVARIANCE", "BUDGETPCTVARIANCE", "FORECASTVARIANCE",
}


class FunctionRegistry:
    """Registry of all BFL functions with metadata."""

    FUNCTIONS: dict[str, dict[str, Any]] = {}

    @classmethod
    def register(cls, name: str, arg_count: int, return_type: str) -> None:
        cls.FUNCTIONS[name.upper()] = {"args": arg_count, "returns": return_type}

    @classmethod
    def get(cls, name: str) -> Optional[dict[str, Any]]:
        return cls.FUNCTIONS.get(name.upper())

    @classmethod
    def suggest(cls, name: str) -> list[str]:
        upper = name.upper()
        return [n for n in cls.FUNCTIONS if upper in n or n in upper]

    @classmethod
    def all_names(cls) -> list[str]:
        return sorted(cls.FUNCTIONS.keys())


# ── Register core functions at module load ───

def _register_core_functions() -> None:
    R = FunctionRegistry.register

    # Arithmetic
    R("ABS", 1, "number")
    R("ROUND", 2, "number")
    R("ROUNDUP", 2, "number")
    R("ROUNDDOWN", 2, "number")
    R("FLOOR", 1, "number")
    R("CEILING", 1, "number")
    R("MOD", 2, "number")
    R("POWER", 2, "number")
    R("SQRT", 1, "number")
    R("LOG", 1, "number")
    R("EXP", 1, "number")

    # Aggregation
    R("SUM", 1, "number")
    R("AVG", 1, "number")
    R("COUNT", 1, "number")
    R("COUNT_DISTINCT", 1, "number")
    R("MIN", 1, "number")
    R("MAX", 1, "number")
    R("FIRST", 1, "number")
    R("LAST", 1, 1)
    R("MEDIAN", 1, "number")
    R("STDDEV", 1, "number")

    # Conditional
    R("IF", 3, "any")
    R("IFS", -1, "any")  # variadic
    R("SWITCH", -1, "any")
    R("ISBLANK", 1, "boolean")
    R("ISERROR", 1, "boolean")
    R("IFERROR", 2, "any")

    # Time intelligence
    R("YTD", 1, "number")
    R("MTD", 1, "number")
    R("QTD", 1, "number")
    R("PY", 1, "number")
    R("PM", 1, "number")
    R("PQ", 1, "number")
    R("YOY", 1, "number")
    R("MOM", 1, "number")
    R("QOQ", 1, "number")
    R("ROLLING3", 1, "number")
    R("ROLLING6", 1, "number")
    R("ROLLING12", 1, "number")

    # Running totals
    R("RUNNING_SUM", 1, "number")
    R("RUNNING_AVG", 1, "number")

    # Ranking
    R("RANK", 1, "number")
    R("RANKDENSE", 1, "number")

    # Percentages
    R("PCTOF", 2, "number")
    R("PCTCHANGE", 2, "number")

    # Financial
    R("BUDGETVARIANCE", 2, "number")
    R("BUDGETPCTVARIANCE", 2, "number")
    R("FORECASTVARIANCE", 2, "number")

    # Logical (also usable as functions)
    R("AND", 2, "boolean")
    R("OR", 2, "boolean")
    R("NOT", 1, "boolean")


_register_core_functions()


# ─────────────────────────────────────────────
# Formula Builder  (fluent API)
# ─────────────────────────────────────────────

class FormulaBuilder:
    """Fluent API for building BFL ASTs programmatically."""

    @staticmethod
    def literal(value: Any) -> FormulaExpression:
        if isinstance(value, str):
            return FormulaExpression(FormulaNodeType.LITERAL_STRING, value)
        return FormulaExpression(FormulaNodeType.LITERAL_NUMBER, str(value))

    @staticmethod
    def metric(name: str) -> FormulaExpression:
        return FormulaExpression(FormulaNodeType.IDENTIFIER, name)

    @staticmethod
    def add(left: FormulaExpression, right: FormulaExpression) -> FormulaExpression:
        return FormulaExpression(FormulaNodeType.BINARY_OP, "+", (left, right))

    @staticmethod
    def sub(left: FormulaExpression, right: FormulaExpression) -> FormulaExpression:
        return FormulaExpression(FormulaNodeType.BINARY_OP, "-", (left, right))

    @staticmethod
    def mul(left: FormulaExpression, right: FormulaExpression) -> FormulaExpression:
        return FormulaExpression(FormulaNodeType.BINARY_OP, "*", (left, right))

    @staticmethod
    def div(left: FormulaExpression, right: FormulaExpression) -> FormulaExpression:
        return FormulaExpression(FormulaNodeType.BINARY_OP, "/", (left, right))

    @staticmethod
    def agg(agg_type: AggregationType, metric_name: str) -> FormulaExpression:
        metric = FormulaExpression(FormulaNodeType.IDENTIFIER, metric_name)
        return FormulaExpression(FormulaNodeType.AGGREGATION, agg_type.value.upper(), (metric,))

    @staticmethod
    def if_expr(
        condition: FormulaExpression,
        true_val: FormulaExpression,
        false_val: FormulaExpression,
    ) -> FormulaExpression:
        return FormulaExpression(
            FormulaNodeType.CONDITIONAL, "IF", (condition, true_val, false_val)
        )

    @staticmethod
    def time_intel(func_name: str, metric_name: str) -> FormulaExpression:
        metric = FormulaExpression(FormulaNodeType.IDENTIFIER, metric_name)
        return FormulaExpression(FormulaNodeType.TIME_INTELLIGENCE, func_name.upper(), (metric,))


# ─────────────────────────────────────────────
# Formula Evaluator
# ─────────────────────────────────────────────

class FormulaEvaluator:
    """Evaluate an AST against concrete data (for testing / validation)."""

    def evaluate(self, ast: FormulaExpression, context: dict[str, Any]) -> Decimal:
        return self._eval(ast, context)

    def _eval(self, node: FormulaExpression, ctx: dict[str, Any]) -> Decimal:
        # ── literals ─────────────────────────
        if node.node_type == FormulaNodeType.LITERAL_NUMBER:
            return Decimal(str(node.value))
        if node.node_type == FormulaNodeType.LITERAL_STRING:
            return Decimal("0")  # strings coerce to 0 in numeric context

        # ── identifier ───────────────────────
        if node.node_type == FormulaNodeType.IDENTIFIER:
            val = ctx.get(node.value, ctx.get(node.value.upper(), Decimal("0")))
            return Decimal(str(val))

        # ── binary op ────────────────────────
        if node.node_type == FormulaNodeType.BINARY_OP:
            left = self._eval(node.children[0], ctx)
            right = self._eval(node.children[1], ctx)
            op = node.value
            if op == "+":
                return left + right
            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    return Decimal("Infinity")
                return left / right
            if op == "%":
                if right == 0:
                    return Decimal("Infinity")
                return left % right
            if op == "AND":
                return Decimal("1") if (left != 0 and right != 0) else Decimal("0")
            if op == "OR":
                return Decimal("1") if (left != 0 or right != 0) else Decimal("0")
            return Decimal("0")

        # ── unary op ─────────────────────────
        if node.node_type == FormulaNodeType.UNARY_OP:
            operand = self._eval(node.children[0], ctx)
            if node.value == "-":
                return -operand
            if node.value == "NOT":
                return Decimal("0") if operand != 0 else Decimal("1")
            return operand

        # ── comparison ────────────────────────
        if node.node_type == FormulaNodeType.COMPARISON:
            left = self._eval(node.children[0], ctx)
            right = self._eval(node.children[1], ctx)
            ops = {
                "=": left == right,
                "!=": left != right,
                "<": left < right,
                ">": left > right,
                "<=": left <= right,
                ">=": left >= right,
            }
            return Decimal("1") if ops.get(node.value, False) else Decimal("0")

        # ── conditional ──────────────────────
        if node.node_type == FormulaNodeType.CONDITIONAL:
            return self._eval_conditional(node, ctx)

        # ── aggregation ──────────────────────
        if node.node_type == FormulaNodeType.AGGREGATION:
            return self._eval_aggregation(node, ctx)

        # ── time intelligence ─────────────────
        if node.node_type == FormulaNodeType.TIME_INTELLIGENCE:
            return self._eval_time_intel(node, ctx)

        # ── function call (arithmetic helpers)
        if node.node_type == FormulaNodeType.FUNCTION_CALL:
            return self._eval_function(node, ctx)

        return Decimal("0")

    # ── conditional ──────────────────────────
    def _eval_conditional(
        self, node: FormulaExpression, ctx: dict[str, Any]
    ) -> Decimal:
        fn = node.value.upper()
        if fn == "IF":
            cond = self._eval(node.children[0], ctx)
            if cond != 0:
                return self._eval(node.children[1], ctx)
            return self._eval(node.children[2], ctx)
        if fn == "IFS":
            for i in range(0, len(node.children) - 1, 2):
                cond = self._eval(node.children[i], ctx)
                if cond != 0:
                    return self._eval(node.children[i + 1], ctx)
            if len(node.children) % 2 == 1:
                return self._eval(node.children[-1], ctx)
            return Decimal("0")
        if fn == "ISBLANK":
            return Decimal("1") if ctx.get(node.children[0].value) is None else Decimal("0")
        if fn == "ISERROR":
            try:
                self._eval(node.children[0], ctx)
                return Decimal("0")
            except Exception:
                return Decimal("1")
        if fn == "IFERROR":
            try:
                return self._eval(node.children[0], ctx)
            except Exception:
                return self._eval(node.children[1], ctx)
        return Decimal("0")

    # ── aggregation ──────────────────────────
    def _eval_aggregation(
        self, node: FormulaExpression, ctx: dict[str, Any]
    ) -> Decimal:
        fn = node.value.upper()
        inner = node.children[0]

        if inner.node_type == FormulaNodeType.IDENTIFIER:
            raw = ctx.get(inner.value, ctx.get(inner.value.upper()))
            if raw is None:
                return Decimal("0")
            if isinstance(raw, list):
                values = [Decimal(str(v)) for v in raw]
            else:
                values = [Decimal(str(raw))]
        else:
            values = [self._eval(inner, ctx)]

        if fn == "SUM":
            return sum(values, Decimal("0"))
        if fn == "AVG":
            return sum(values, Decimal("0")) / len(values) if values else Decimal("0")
        if fn == "COUNT":
            return Decimal(str(len(values)))
        if fn == "COUNT_DISTINCT":
            return Decimal(str(len(set(values))))
        if fn == "MIN":
            return min(values) if values else Decimal("0")
        if fn == "MAX":
            return max(values) if values else Decimal("0")
        if fn == "MEDIAN":
            s = sorted(values)
            n = len(s)
            if n == 0:
                return Decimal("0")
            mid = n // 2
            if n % 2 == 1:
                return s[mid]
            return (s[mid - 1] + s[mid]) / 2
        if fn == "STDDEV":
            if len(values) < 2:
                return Decimal("0")
            mean = sum(values, Decimal("0")) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
            return variance.sqrt()
        if fn == "FIRST":
            return values[0] if values else Decimal("0")
        if fn == "LAST":
            return values[-1] if values else Decimal("0")
        return values[0] if values else Decimal("0")

    # ── time intelligence ────────────────────
    def _eval_time_intel(
        self, node: FormulaExpression, ctx: dict[str, Any]
    ) -> Decimal:
        fn = node.value.upper()
        metric = node.children[0].value if node.children else ""

        current_val = ctx.get(metric, ctx.get(metric.upper(), Decimal("0")))
        if isinstance(current_val, list):
            current_val = sum(Decimal(str(v)) for v in current_val)

        if fn == "PY":
            return Decimal(str(ctx.get("_prev_value", ctx.get("_prev_value", current_val))))
        if fn == "PM":
            return Decimal(str(ctx.get("_prev_value", ctx.get("_prev_value", current_val))))
        if fn == "PQ":
            return Decimal(str(ctx.get("_prev_value", ctx.get("_prev_value", current_val))))
        if fn == "YOY":
            prev = ctx.get("_prev_value", current_val)
            return Decimal(str(current_val)) - Decimal(str(prev))
        if fn == "MOM":
            prev = ctx.get("_prev_value", current_val)
            return Decimal(str(current_val)) - Decimal(str(prev))
        if fn == "QOQ":
            prev = ctx.get("_prev_value", current_val)
            return Decimal(str(current_val)) - Decimal(str(prev))
        return Decimal(str(current_val))

    # ── function call ────────────────────────
    def _eval_function(
        self, node: FormulaExpression, ctx: dict[str, Any]
    ) -> Decimal:
        fn = node.value.upper()
        args = [self._eval(a, ctx) for a in node.children]

        if fn == "ABS":
            return abs(args[0])
        if fn == "ROUND":
            return args[0].quantize(Decimal(10) ** -int(args[1]), rounding=ROUND_HALF_UP)
        if fn == "ROUNDUP":
            return args[0].quantize(Decimal(10) ** -int(args[1]), rounding="ROUND_HALF_UP")
        if fn == "ROUNDDOWN":
            return args[0].quantize(Decimal(10) ** -int(args[1]), rounding="ROUND_DOWN")
        if fn == "FLOOR":
            return args[0].to_integral_value(rounding="ROUND_FLOOR")
        if fn == "CEILING":
            return args[0].to_integral_value(rounding="ROUND_CEILING")
        if fn == "MOD":
            return args[0] % args[1] if len(args) > 1 and args[1] != 0 else Decimal("0")
        if fn == "POWER":
            return args[0] ** int(args[1]) if len(args) > 1 else args[0]
        if fn == "SQRT":
            return args[0].sqrt() if args[0] >= 0 else Decimal("0")
        if fn == "LOG":
            import math
            return Decimal(str(math.log(float(args[0])))) if args[0] > 0 else Decimal("0")
        if fn == "EXP":
            import math
            return Decimal(str(math.exp(float(args[0]))))
        return args[0] if args else Decimal("0")


# ─────────────────────────────────────────────
# Convenience: parse text → AST in one call
# ─────────────────────────────────────────────

def parse_formula(text: str) -> FormulaExpression:
    """Tokenize and parse a BFL expression string into an AST."""
    lexer = FormulaLexer()
    parser = FormulaParser()
    tokens = lexer.tokenize(text)
    return parser.parse(tokens)


# ─────────────────────────────────────────────
# Convenience: parse → validate → SQL in one call
# ─────────────────────────────────────────────

def compile_formula(
    text: str,
    dialect: SQLDialect = SQLDialect.POSTGRESQL,
    known_metrics: Optional[dict[str, str]] = None,
    metric_table: str = "metrics",
    date_column: str = "transaction_date",
) -> tuple[Optional[FormulaExpression], list[FormulaError], str]:
    """
    Full compilation pipeline: tokenize → parse → validate → generate SQL.
    Returns (ast, errors, sql).  If errors is non-empty, sql may be partial.
    """
    ast = parse_formula(text)
    analyzer = FormulaSemanticAnalyzer()
    errors = analyzer.analyze(ast, known_metrics)
    gen = FormulaSQLGenerator()
    sql = gen.generate(ast, dialect, metric_table, date_column)
    return ast, errors, sql
