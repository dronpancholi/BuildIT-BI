from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

class Cardinality(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class SCDType(Enum):
    SCD0 = "scd0"
    SCD1 = "scd1"
    SCD2 = "scd2"
    SCD3 = "scd3"

class JoinType(Enum):
    INNER = "inner"
    LEFT = "left"
    RIGHT = "right"

class PartitionType(Enum):
    DATE = "date"
    HASH = "hash"
    LIST = "list"

@dataclass
class DimensionValue:
    dimension_id: UUID = field(default_factory=uuid4)
    key: str = ""
    name: str = ""
    description: Optional[str] = None
    attributes: dict = field(default_factory=dict)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    is_current: bool = True
    is_deleted: bool = False

@dataclass
class Dimension:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    physical_name: str = ""
    cardinality: Cardinality = Cardinality.MEDIUM
    key_column: str = ""
    name_column: str = ""
    description_column: Optional[str] = None
    scd_type: SCDType = SCDType.SCD0
    valid_from_column: Optional[str] = None
    valid_to_column: Optional[str] = None
    surrogate_key_column: Optional[str] = None
    is_sensitive: bool = False
    row_level_security_column: Optional[str] = None
    default_hierarchy_id: Optional[UUID] = None
    tags: list[str] = field(default_factory=list)
    owner_id: UUID = field(default_factory=uuid4)
    values: list[DimensionValue] = field(default_factory=list)

    def add_value(self, key: str, name: str, attributes: dict = None) -> DimensionValue:
        dv = DimensionValue(dimension_id=self.id, key=key, name=name, attributes=attributes or {})
        self.values.append(dv)
        return dv

    def get_current_values(self) -> list[DimensionValue]:
        return [v for v in self.values if v.is_current and not v.is_deleted]

@dataclass
class HierarchyLevel:
    level_name: str = ""
    dimension_id: UUID = field(default_factory=uuid4)
    key_column: str = ""
    name_column: str = ""

@dataclass
class DimensionHierarchy:
    id: UUID = field(default_factory=uuid4)
    dimension_id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    levels: list[HierarchyLevel] = field(default_factory=list)
    is_default: bool = False
    is_active: bool = True

@dataclass
class DimensionRole:
    id: UUID = field(default_factory=uuid4)
    dimension_id: UUID = field(default_factory=uuid4)
    role_name: str = ""
    role_description: str = ""
    join_column: str = ""
    default_filter: Optional[dict] = None

@dataclass
class FactColumn:
    name: str = ""
    data_type: str = "DECIMAL(18,2)"
    nullable: bool = True
    is_measure: bool = False
    is_dimension_key: bool = False
    description: Optional[str] = None

@dataclass
class DimensionRoleBinding:
    role_id: UUID = field(default_factory=uuid4)
    dimension_id: UUID = field(default_factory=uuid4)
    join_type: JoinType = JoinType.INNER
    join_condition: str = ""

@dataclass
class FactTable:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    slug: str = ""
    physical_name: str = ""
    columns: list[FactColumn] = field(default_factory=list)
    grain: str = ""
    grain_columns: list[str] = field(default_factory=list)
    dimension_roles: list[DimensionRoleBinding] = field(default_factory=list)
    partition_column: Optional[str] = None
    partition_type: Optional[PartitionType] = None
    cluster_columns: list[str] = field(default_factory=list)
    data_source: str = ""
    refresh_frequency: str = "daily"
    last_refreshed_at: Optional[datetime] = None
    row_count: Optional[int] = None
    tags: list[str] = field(default_factory=list)
    owner_id: UUID = field(default_factory=uuid4)

    def add_column(self, **kwargs) -> FactColumn:
        col = FactColumn(**kwargs)
        self.columns.append(col)
        return col

    def get_measures(self) -> list[FactColumn]:
        return [c for c in self.columns if c.is_measure]

    def get_dimension_keys(self) -> list[FactColumn]:
        return [c for c in self.columns if c.is_dimension_key]

@dataclass
class SemanticRelationship:
    id: UUID = field(default_factory=uuid4)
    source_table: str = ""
    target_table: str = ""
    join_type: JoinType = JoinType.INNER
    join_condition: str = ""
    source_cardinality: Cardinality = Cardinality.MEDIUM
    target_cardinality: Cardinality = Cardinality.MEDIUM
    is_one_to_one: bool = False
    is_optional: bool = False
    is_conformed: bool = False
    conformed_name: Optional[str] = None

@dataclass
class SemanticAlias:
    id: UUID = field(default_factory=uuid4)
    canonical_name: str = ""
    alias: str = ""
    entity_type: str = ""
    entity_id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    usage_count: int = 0

@dataclass
class SCD2Record:
    surrogate_key: int = 0
    natural_key: str = ""
    attributes: dict = field(default_factory=dict)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    version: int = 1
    is_current: bool = True

class SemanticLayerService:
    def __init__(self):
        self.dimensions: dict[UUID, Dimension] = {}
        self.fact_tables: dict[UUID, FactTable] = {}
        self.hierarchies: dict[UUID, DimensionHierarchy] = {}
        self.relationships: list[SemanticRelationship] = []
        self.aliases: dict[str, SemanticAlias] = {}
        self.scd2_records: dict[str, list[SCD2Record]] = {}

    def create_dimension(self, **kwargs) -> Dimension:
        dim = Dimension(**kwargs)
        self.dimensions[dim.id] = dim
        return dim

    def create_fact_table(self, **kwargs) -> FactTable:
        fact = FactTable(**kwargs)
        self.fact_tables[fact.id] = fact
        return fact

    def add_hierarchy(self, dimension_id: UUID, name: str, levels: list[dict]) -> DimensionHierarchy:
        hierarchy_levels = [HierarchyLevel(**l) for l in levels]
        h = DimensionHierarchy(dimension_id=dimension_id, name=name, levels=hierarchy_levels)
        self.hierarchies[h.id] = h
        return h

    def add_relationship(self, **kwargs) -> SemanticRelationship:
        rel = SemanticRelationship(**kwargs)
        self.relationships.append(rel)
        return rel

    def add_alias(self, canonical_name: str, alias: str, entity_type: str, entity_id: UUID) -> SemanticAlias:
        sa = SemanticAlias(canonical_name=canonical_name, alias=alias, entity_type=entity_type, entity_id=entity_id)
        self.aliases[alias.lower()] = sa
        return sa

    def resolve_alias(self, name: str) -> Optional[str]:
        sa = self.aliases.get(name.lower())
        return sa.canonical_name if sa else name

    def add_scd2_record(self, dimension_slug: str, natural_key: str, attributes: dict, valid_from: datetime) -> SCD2Record:
        records = self.scd2_records.setdefault(dimension_slug, [])
        for r in records:
            if r.natural_key == natural_key and r.is_current:
                r.valid_to = valid_from
                r.is_current = False
                r.version += 1
        new_record = SCD2Record(
            surrogate_key=len(records) + 1,
            natural_key=natural_key,
            attributes=attributes,
            valid_from=valid_from,
            is_current=True,
            version=len([r for r in records if r.natural_key == natural_key]) + 1,
        )
        records.append(new_record)
        return new_record

    def get_current_scd2(self, dimension_slug: str, natural_key: str) -> Optional[SCD2Record]:
        records = self.scd2_records.get(dimension_slug, [])
        for r in records:
            if r.natural_key == natural_key and r.is_current:
                return r
        return None

    def get_historical_scd2(self, dimension_slug: str, natural_key: str, as_of: datetime) -> Optional[SCD2Record]:
        records = self.scd2_records.get(dimension_slug, [])
        for r in records:
            if r.natural_key == natural_key and r.valid_from <= as_of and (r.valid_to is None or r.valid_to > as_of):
                return r
        return None

    def get_dimension(self, dimension_id: UUID) -> Optional[Dimension]:
        return self.dimensions.get(dimension_id)

    def list_dimensions(self, cardinality: Optional[Cardinality] = None) -> list[Dimension]:
        dims = list(self.dimensions.values())
        if cardinality:
            dims = [d for d in dims if d.cardinality == cardinality]
        return dims

    def list_fact_tables(self) -> list[FactTable]:
        return list(self.fact_tables.values())

    def find_relationships(self, source_table: str, target_table: str) -> list[SemanticRelationship]:
        return [r for r in self.relationships if r.source_table == source_table and r.target_table == target_table]
