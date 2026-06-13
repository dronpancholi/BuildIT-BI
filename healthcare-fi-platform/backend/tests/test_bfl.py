import pytest
from uuid import uuid4
from app.domain.bfl import (
    FormulaLexer, FormulaParser, FormulaSQLGenerator, FormulaSemanticAnalyzer,
    FunctionRegistry, FormulaBuilder, Formula, FormulaStatus, AggregationType,
    SQLDialect, FormulaNodeType, TokenType, SourceSpan, FormulaExpression
)

class TestFormulaLexer:
    def test_tokenize_simple_number(self):
        lexer = FormulaLexer()
        tokens = lexer.tokenize("42")
        assert len(tokens) == 2  # number + EOF
        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "42"

    def test_tokenize_arithmetic(self):
        lexer = FormulaLexer()
        tokens = lexer.tokenize("a + b * c")
        types = [t.type for t in tokens[:-1]]  # exclude EOF
        assert types == [TokenType.IDENT, TokenType.PLUS, TokenType.IDENT, TokenType.STAR, TokenType.IDENT]

    def test_tokenize_function_call(self):
        lexer = FormulaLexer()
        tokens = lexer.tokenize("SUM(Revenue)")
        assert tokens[0].type == TokenType.IDENT
        assert tokens[0].value == "SUM"
        assert tokens[1].type == TokenType.LPAREN
        assert tokens[2].type == TokenType.IDENT
        assert tokens[3].type == TokenType.RPAREN

    def test_tokenize_comparison(self):
        lexer = FormulaLexer()
        tokens = lexer.tokenize("x >= 100")
        assert tokens[1].type == TokenType.GTE

    def test_tokenize_string(self):
        lexer = FormulaLexer()
        tokens = lexer.tokenize('"hello"')
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello"

    def test_tokenize_complex_expression(self):
        lexer = FormulaLexer()
        tokens = lexer.tokenize("IF(AR_DAYS > 90, HIGH, LOW)")
        assert len(tokens) > 5

    def test_tokenize_keywords(self):
        lexer = FormulaLexer()
        tokens = lexer.tokenize("a AND b OR NOT c")
        types = [t.type for t in tokens[:-1]]
        assert TokenType.AND in types
        assert TokenType.OR in types
        assert TokenType.NOT in types

class TestFormulaParser:
    def test_parse_literal(self):
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("42")
        ast = parser.parse(tokens)
        assert ast.node_type == FormulaNodeType.LITERAL_NUMBER
        assert ast.value == "42"

    def test_parse_identifier(self):
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("Revenue")
        ast = parser.parse(tokens)
        assert ast.node_type == FormulaNodeType.IDENTIFIER
        assert ast.value == "Revenue"

    def test_parse_addition(self):
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("a + b")
        ast = parser.parse(tokens)
        assert ast.node_type == FormulaNodeType.BINARY_OP
        assert ast.value == "+"
        assert len(ast.children) == 2

    def test_parse_operator_precedence(self):
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("a + b * c")
        ast = parser.parse(tokens)
        # Should be a + (b * c), so root is +
        assert ast.value == "+"
        # Right child should be *
        assert ast.children[1].value == "*"

    def test_parse_parentheses(self):
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("(a + b) * c")
        ast = parser.parse(tokens)
        assert ast.value == "*"
        assert ast.children[0].value == "+"

    def test_parse_function_call(self):
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("SUM(Revenue)")
        ast = parser.parse(tokens)
        # SUM is recognized as AGGREGATION by the parser
        assert ast.node_type in (FormulaNodeType.FUNCTION_CALL, FormulaNodeType.AGGREGATION)
        assert ast.value == "SUM"

    def test_parse_comparison(self):
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("x > 100")
        ast = parser.parse(tokens)
        assert ast.node_type == FormulaNodeType.COMPARISON
        assert ast.value == ">"

    def test_parse_if_conditional(self):
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("IF(x > 10, 'high', 'low')")
        ast = parser.parse(tokens)
        assert ast.node_type == FormulaNodeType.CONDITIONAL

    def test_parse_nested_function(self):
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("SUM(Revenue) / COUNT(Patients)")
        ast = parser.parse(tokens)
        assert ast.value == "/"

class TestFormulaSQLGenerator:
    def test_generate_literal(self):
        gen = FormulaSQLGenerator()
        ast = FormulaExpression(FormulaNodeType.LITERAL_NUMBER, "42")
        sql = gen.generate(ast)
        assert "42" in sql

    def test_generate_identifier(self):
        gen = FormulaSQLGenerator()
        ast = FormulaExpression(FormulaNodeType.IDENTIFIER, "Revenue")
        sql = gen.generate(ast)
        assert "Revenue" in sql

    def test_generate_addition(self):
        gen = FormulaSQLGenerator()
        left = FormulaExpression(FormulaNodeType.IDENTIFIER, "a")
        right = FormulaExpression(FormulaNodeType.IDENTIFIER, "b")
        ast = FormulaExpression(FormulaNodeType.BINARY_OP, "+", (left, right))
        sql = gen.generate(ast)
        assert "+" in sql

    def test_generate_sum_aggregation(self):
        gen = FormulaSQLGenerator()
        ast = FormulaExpression(FormulaNodeType.AGGREGATION, "SUM",
            (FormulaExpression(FormulaNodeType.IDENTIFIER, "Revenue"),))
        sql = gen.generate(ast)
        assert "SUM" in sql.upper()

    def test_generate_if_conditional(self):
        gen = FormulaSQLGenerator()
        cond = FormulaExpression(FormulaNodeType.COMPARISON, ">",
            (FormulaExpression(FormulaNodeType.IDENTIFIER, "x"),
             FormulaExpression(FormulaNodeType.LITERAL_NUMBER, "10")))
        true_val = FormulaExpression(FormulaNodeType.LITERAL_NUMBER, "1")
        false_val = FormulaExpression(FormulaNodeType.LITERAL_NUMBER, "0")
        ast = FormulaExpression(FormulaNodeType.CONDITIONAL, "IF", (cond, true_val, false_val))
        sql = gen.generate(ast)
        assert "CASE" in sql.upper() or "IF" in sql.upper()

    def test_generate_postgresql_dialect(self):
        gen = FormulaSQLGenerator()
        ast = FormulaExpression(FormulaNodeType.IDENTIFIER, "Revenue")
        sql = gen.generate(ast, dialect=SQLDialect.POSTGRESQL)
        assert isinstance(sql, str)

    def test_generate_snowflake_dialect(self):
        gen = FormulaSQLGenerator()
        ast = FormulaExpression(FormulaNodeType.IDENTIFIER, "Revenue")
        sql = gen.generate(ast, dialect=SQLDialect.SNOWFLAKE)
        assert isinstance(sql, str)

class TestFormulaSemanticAnalyzer:
    def test_valid_expression_no_errors(self):
        analyzer = FormulaSemanticAnalyzer()
        ast = FormulaExpression(FormulaNodeType.IDENTIFIER, "Revenue")
        errors = analyzer.analyze(ast, known_metrics={"REVENUE": "decimal"})
        assert len(errors) == 0

    def test_unknown_function_error(self):
        analyzer = FormulaSemanticAnalyzer()
        ast = FormulaExpression(FormulaNodeType.FUNCTION_CALL, "NONEXISTENT",
            (FormulaExpression(FormulaNodeType.IDENTIFIER, "x"),))
        errors = analyzer.analyze(ast, known_metrics={"X": "decimal"})
        assert len(errors) > 0
        assert errors[0].code in ("UNKNOWN_FUNCTION", "BFL002")

class TestFunctionRegistry:
    def test_register_and_lookup(self):
        FunctionRegistry.register("CUSTOM_FUNC", 2, "number")
        result = FunctionRegistry.get("CUSTOM_FUNC")
        assert result is not None
        assert result["args"] == 2

    def test_suggest_similar(self):
        suggestions = FunctionRegistry.suggest("RUN")
        assert len(suggestions) > 0

    def test_all_names_returns_list(self):
        names = FunctionRegistry.all_names()
        assert "SUM" in names
        assert "AVG" in names
        assert "IF" in names
        assert len(names) >= 50

class TestFormulaBuilder:
    def test_literal(self):
        ast = FormulaBuilder.literal(42)
        assert ast.node_type == FormulaNodeType.LITERAL_NUMBER

    def test_metric(self):
        ast = FormulaBuilder.metric("Revenue")
        assert ast.node_type == FormulaNodeType.IDENTIFIER
        assert ast.value == "Revenue"

    def test_add(self):
        a = FormulaBuilder.literal(1)
        b = FormulaBuilder.literal(2)
        ast = FormulaBuilder.add(a, b)
        assert ast.value == "+"

    def test_agg(self):
        ast = FormulaBuilder.agg(AggregationType.SUM, "Revenue")
        assert ast.node_type == FormulaNodeType.AGGREGATION
        assert ast.value == "SUM"

    def test_if_expr(self):
        cond = FormulaExpression(FormulaNodeType.COMPARISON, ">",
            (FormulaBuilder.metric("x"), FormulaBuilder.literal(10)))
        ast = FormulaBuilder.if_expr(cond, FormulaBuilder.literal(1), FormulaBuilder.literal(0))
        assert ast.node_type == FormulaNodeType.CONDITIONAL

class TestFormula:
    def test_create_formula(self):
        f = Formula(name="Revenue YTD", slug="revenue_ytd", expression_text="SUM(Revenue)")
        assert f.status == FormulaStatus.DRAFT
        assert f.version == 1

    def test_publish_formula(self):
        f = Formula(name="Revenue YTD", expression_text="SUM(Revenue)")
        f.status = FormulaStatus.PUBLISHED
        f.published_at = __import__("datetime").datetime.utcnow()
        assert f.status == FormulaStatus.PUBLISHED

    def test_deprecate_formula(self):
        f = Formula(name="Old Metric", expression_text="SUM(Revenue)")
        f.status = FormulaStatus.DEPRECATED
        f.deprecated_at = __import__("datetime").datetime.utcnow()
        assert f.status == FormulaStatus.DEPRECATED

class TestHealthcareFormula:
    def test_revenue_formula(self):
        """Test the key healthcare financial formula"""
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("SUM(Gross_Charges) - SUM(Contractual_Adjustments) - SUM(Charity_Care) - SUM(Bad_Debt)")
        ast = parser.parse(tokens)
        assert ast.value == "-"
        # Should be nested subtraction
        assert ast.children[0].value == "-"

    def test_ar_days_formula(self):
        """AR Days = Gross AR / (Revenue / 365)"""
        lexer = FormulaLexer()
        parser = FormulaParser()
        tokens = lexer.tokenize("Gross_AR / (Revenue / 365)")
        ast = parser.parse(tokens)
        assert ast.value == "/"
