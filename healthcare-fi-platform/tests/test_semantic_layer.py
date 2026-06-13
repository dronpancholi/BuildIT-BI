import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.domain.semantic_layer import (
    Cardinality,
    SCDType,
    JoinType,
    PartitionType,
    Dimension,
    DimensionValue,
    DimensionHierarchy,
    HierarchyLevel,
    DimensionRole,
    FactColumn,
    DimensionRoleBinding,
    FactTable,
    SemanticRelationship,
    SemanticAlias,
    SCD2Record,
    SemanticLayerService,
)


class TestDimension:
    def test_create_dimension_defaults(self):
        dim = Dimension(name="Provider", slug="provider")
        assert dim.name == "Provider"
        assert dim.cardinality == Cardinality.MEDIUM
        assert dim.scd_type == SCDType.SCD0

    def test_add_value(self):
        dim = Dimension(name="Provider", slug="provider")
        dv = dim.add_value(key="P001", name="Dr. Smith", attributes={"specialty": "Cardiology"})
        assert dv.key == "P001"
        assert dv.name == "Dr. Smith"
        assert dv.attributes["specialty"] == "Cardiology"
        assert len(dim.values) == 1

    def test_get_current_values(self):
        dim = Dimension(name="Dept", slug="dept")
        dim.add_value(key="D1", name="Cardiology")
        old = DimensionValue(dimension_id=dim.id, key="D2", name="Old", is_current=False)
        dim.values.append(old)
        deleted = DimensionValue(dimension_id=dim.id, key="D3", name="Gone", is_deleted=True)
        dim.values.append(deleted)

        current = dim.get_current_values()
        assert len(current) == 1
        assert current[0].key == "D1"

    def test_add_multiple_values(self):
        dim = Dimension(name="Unit", slug="unit")
        for i in range(5):
            dim.add_value(key=f"U{i}", name=f"Unit {i}")
        assert len(dim.values) == 5


class TestSCD2:
    def test_add_record(self):
        svc = SemanticLayerService()
        record = svc.add_scd2_record(
            dimension_slug="provider",
            natural_key="P001",
            attributes={"name": "Dr. Smith", "specialty": "Cardiology"},
            valid_from=datetime(2024, 1, 1),
        )
        assert record.natural_key == "P001"
        assert record.is_current is True
        assert record.version == 1

    def test_get_current(self):
        svc = SemanticLayerService()
        svc.add_scd2_record(
            dimension_slug="provider",
            natural_key="P001",
            attributes={"name": "Dr. Smith"},
            valid_from=datetime(2024, 1, 1),
        )
        current = svc.get_current_scd2("provider", "P001")
        assert current is not None
        assert current.attributes["name"] == "Dr. Smith"

    def test_get_current_nonexistent(self):
        svc = SemanticLayerService()
        assert svc.get_current_scd2("provider", "MISSING") is None

    def test_version_increment(self):
        svc = SemanticLayerService()
        svc.add_scd2_record(
            dimension_slug="provider",
            natural_key="P001",
            attributes={"name": "Dr. Smith"},
            valid_from=datetime(2024, 1, 1),
        )
        updated = svc.add_scd2_record(
            dimension_slug="provider",
            natural_key="P001",
            attributes={"name": "Dr. Smith-Jones"},
            valid_from=datetime(2024, 6, 1),
        )
        assert updated.version == 2
        assert updated.attributes["name"] == "Dr. Smith-Jones"

    def test_previous_record_closed(self):
        svc = SemanticLayerService()
        svc.add_scd2_record(
            dimension_slug="provider",
            natural_key="P001",
            attributes={"name": "Dr. Smith"},
            valid_from=datetime(2024, 1, 1),
        )
        svc.add_scd2_record(
            dimension_slug="provider",
            natural_key="P001",
            attributes={"name": "Dr. Smith-Jones"},
            valid_from=datetime(2024, 6, 1),
        )
        old = svc.get_historical_scd2("provider", "P001", as_of=datetime(2024, 3, 15))
        assert old is not None
        assert old.attributes["name"] == "Dr. Smith"
        assert old.valid_to == datetime(2024, 6, 1)

    def test_get_historical_as_of(self):
        svc = SemanticLayerService()
        svc.add_scd2_record(
            dimension_slug="provider",
            natural_key="P001",
            attributes={"name": "Dr. Smith"},
            valid_from=datetime(2024, 1, 1),
        )
        svc.add_scd2_record(
            dimension_slug="provider",
            natural_key="P001",
            attributes={"name": "Dr. Smith-Jones"},
            valid_from=datetime(2024, 6, 1),
        )
        recent = svc.get_historical_scd2("provider", "P001", as_of=datetime(2024, 9, 1))
        assert recent is not None
        assert recent.attributes["name"] == "Dr. Smith-Jones"

    def test_multiple_natural_keys(self):
        svc = SemanticLayerService()
        svc.add_scd2_record("provider", "P001", {"name": "Smith"}, datetime(2024, 1, 1))
        svc.add_scd2_record("provider", "P002", {"name": "Jones"}, datetime(2024, 1, 1))
        assert svc.get_current_scd2("provider", "P001") is not None
        assert svc.get_current_scd2("provider", "P002") is not None

    def test_version_increments_across_updates(self):
        svc = SemanticLayerService()
        for i in range(5):
            svc.add_scd2_record(
                dimension_slug="dept",
                natural_key="D001",
                attributes={"name": f"Dept v{i}"},
                valid_from=datetime(2024, 1, 1) + timedelta(days=i * 30),
            )
        records = svc.scd2_records["dept"]
        d001_records = [r for r in records if r.natural_key == "D001"]
        assert len(d001_records) == 5
        current = svc.get_current_scd2("dept", "D001")
        assert current.version == 5

    def test_historical_no_match(self):
        svc = SemanticLayerService()
        svc.add_scd2_record("provider", "P001", {"name": "Smith"}, datetime(2024, 6, 1))
        result = svc.get_historical_scd2("provider", "P001", as_of=datetime(2024, 1, 1))
        assert result is None


class TestFactTable:
    def test_create_fact(self):
        svc = SemanticLayerService()
        fact = svc.create_fact_table(name="claims", slug="claims", physical_name="f_claims")
        assert fact.name == "claims"
        assert fact.physical_name == "f_claims"

    def test_add_column(self):
        svc = SemanticLayerService()
        fact = svc.create_fact_table(name="claims")
        col = fact.add_column(name="amount", data_type="DECIMAL(18,2)", is_measure=True)
        assert col.name == "amount"
        assert col.is_measure is True

    def test_get_measures(self):
        svc = SemanticLayerService()
        fact = svc.create_fact_table(name="claims")
        fact.add_column(name="claim_id", is_dimension_key=True)
        fact.add_column(name="amount", is_measure=True)
        fact.add_column(name="charge", is_measure=True)
        measures = fact.get_measures()
        assert len(measures) == 2

    def test_get_dimension_keys(self):
        svc = SemanticLayerService()
        fact = svc.create_fact_table(name="claims")
        fact.add_column(name="claim_id", is_dimension_key=True)
        fact.add_column(name="amount", is_measure=True)
        fact.add_column(name="provider_id", is_dimension_key=True)
        keys = fact.get_dimension_keys()
        assert len(keys) == 2

    def test_list_fact_tables(self):
        svc = SemanticLayerService()
        svc.create_fact_table(name="claims")
        svc.create_fact_table(name="encounters")
        facts = svc.list_fact_tables()
        assert len(facts) == 2


class TestHierarchy:
    def test_add_hierarchy(self):
        svc = SemanticLayerService()
        dim = svc.create_dimension(name="Provider", slug="provider")
        levels = [
            {"level_name": "region", "dimension_id": str(dim.id), "key_column": "region_id", "name_column": "region_name"},
            {"level_name": "facility", "dimension_id": str(dim.id), "key_column": "facility_id", "name_column": "facility_name"},
        ]
        h = svc.add_hierarchy(dim.id, name="Region-Facility", levels=levels)
        assert h.name == "Region-Facility"
        assert len(h.levels) == 2
        assert h.levels[0].level_name == "region"


class TestRelationship:
    def test_add_relationship(self):
        svc = SemanticLayerService()
        rel = svc.add_relationship(
            source_table="f_claims",
            target_table="d_provider",
            join_type=JoinType.INNER,
            join_condition="claims.provider_id = provider.id",
        )
        assert rel.source_table == "f_claims"
        assert rel.target_table == "d_provider"

    def test_find_relationships(self):
        svc = SemanticLayerService()
        svc.add_relationship(source_table="f_claims", target_table="d_provider", join_condition="a.id = b.id")
        svc.add_relationship(source_table="f_claims", target_table="d_payer", join_condition="a.id = c.id")
        results = svc.find_relationships("f_claims", "d_provider")
        assert len(results) == 1
        assert results[0].target_table == "d_provider"


class TestAlias:
    def test_add_alias(self):
        svc = SemanticLayerService()
        dim = svc.create_dimension(name="Provider", slug="provider")
        alias = svc.add_alias("provider", "doctor", "dimension", dim.id)
        assert alias.alias == "doctor"

    def test_resolve_alias(self):
        svc = SemanticLayerService()
        dim = svc.create_dimension(name="Provider", slug="provider")
        svc.add_alias("provider", "doctor", "dimension", dim.id)
        resolved = svc.resolve_alias("doctor")
        assert resolved == "provider"

    def test_resolve_unknown_returns_original(self):
        svc = SemanticLayerService()
        assert svc.resolve_alias("unknown") == "unknown"

    def test_alias_case_insensitive(self):
        svc = SemanticLayerService()
        dim = svc.create_dimension(name="Provider", slug="provider")
        svc.add_alias("provider", "Doctor", "dimension", dim.id)
        assert svc.resolve_alias("DOCTOR") == "provider"
        assert svc.resolve_alias("doctor") == "provider"


class TestDimensionFiltering:
    def test_list_dimensions_all(self):
        svc = SemanticLayerService()
        svc.create_dimension(name="A", cardinality=Cardinality.HIGH)
        svc.create_dimension(name="B", cardinality=Cardinality.LOW)
        svc.create_dimension(name="C", cardinality=Cardinality.MEDIUM)
        assert len(svc.list_dimensions()) == 3

    def test_list_dimensions_by_cardinality(self):
        svc = SemanticLayerService()
        svc.create_dimension(name="A", cardinality=Cardinality.HIGH)
        svc.create_dimension(name="B", cardinality=Cardinality.HIGH)
        svc.create_dimension(name="C", cardinality=Cardinality.LOW)
        high = svc.list_dimensions(cardinality=Cardinality.HIGH)
        assert len(high) == 2
        low = svc.list_dimensions(cardinality=Cardinality.LOW)
        assert len(low) == 1

    def test_get_dimension(self):
        svc = SemanticLayerService()
        dim = svc.create_dimension(name="Provider", slug="provider")
        retrieved = svc.get_dimension(dim.id)
        assert retrieved is dim

    def test_get_dimension_nonexistent(self):
        svc = SemanticLayerService()
        assert svc.get_dimension(uuid4()) is None


class TestSemanticLayerServiceIntegration:
    def test_full_dimension_workflow(self):
        svc = SemanticLayerService()
        dim = svc.create_dimension(
            name="Provider",
            slug="provider",
            physical_name="d_provider",
            cardinality=Cardinality.HIGH,
            key_column="provider_id",
            name_column="provider_name",
            scd_type=SCDType.SCD2,
        )
        assert dim.cardinality == Cardinality.HIGH
        assert dim.scd_type == SCDType.SCD2

        dim.add_value(key="P001", name="Dr. Smith")
        dim.add_value(key="P002", name="Dr. Jones")
        assert len(dim.values) == 2

        h = svc.add_hierarchy(dim.id, name="Region-Facility", levels=[
            {"level_name": "region", "dimension_id": str(dim.id), "key_column": "region_id", "name_column": "region_name"},
        ])
        assert h.dimension_id == dim.id

        svc.add_scd2_record("provider", "P001", {"name": "Dr. Smith"}, datetime(2024, 1, 1))
        svc.add_scd2_record("provider", "P001", {"name": "Dr. Smith Jr."}, datetime(2024, 6, 1))
        current = svc.get_current_scd2("provider", "P001")
        assert current.attributes["name"] == "Dr. Smith Jr."
        assert current.version == 2

    def test_full_fact_workflow(self):
        svc = SemanticLayerService()
        fact = svc.create_fact_table(
            name="Claims",
            slug="claims",
            physical_name="f_claims",
            grain="One row per claim line",
            grain_columns=["claim_line_id"],
        )
        fact.add_column(name="claim_line_id", is_dimension_key=True, data_type="BIGINT")
        fact.add_column(name="provider_id", is_dimension_key=True, data_type="VARCHAR(36)")
        fact.add_column(name="payer_id", is_dimension_key=True, data_type="VARCHAR(36)")
        fact.add_column(name="amount", is_measure=True, data_type="DECIMAL(18,2)")
        fact.add_column(name="quantity", is_measure=True, data_type="INT")
        fact.add_column(name="service_date", data_type="DATE")

        assert len(fact.columns) == 6
        assert len(fact.get_measures()) == 2
        assert len(fact.get_dimension_keys()) == 3

        rel = svc.add_relationship(
            source_table="f_claims",
            target_table="d_provider",
            join_type=JoinType.INNER,
            join_condition="f_claims.provider_id = d_provider.provider_id",
            is_conformed=True,
            conformed_name="provider_conformed",
        )
        assert rel.is_conformed is True

    def test_scenarios_filter(self):
        svc = SemanticLayerService()
        svc.create_dimension(name="A", cardinality=Cardinality.HIGH)
        svc.create_dimension(name="B", cardinality=Cardinality.LOW)
        svc.create_dimension(name="C", cardinality=Cardinality.LOW)

        low_dims = svc.list_dimensions(cardinality=Cardinality.LOW)
        assert all(d.cardinality == Cardinality.LOW for d in low_dims)
        assert len(low_dims) == 2
