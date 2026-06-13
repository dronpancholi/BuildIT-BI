import pytest
from datetime import datetime
from uuid import uuid4
from app.domain.semantic_layer import (
    Dimension, DimensionValue, DimensionHierarchy, HierarchyLevel, DimensionRole,
    FactTable, FactColumn, SemanticRelationship, SemanticAlias, SCD2Record,
    SemanticLayerService, Cardinality, SCDType, JoinType, PartitionType
)

class TestDimension:
    def test_create_dimension(self):
        d = Dimension(name="Department", slug="department", physical_name="departments")
        assert d.cardinality == Cardinality.MEDIUM

    def test_add_value(self):
        d = Dimension(name="Department")
        dv = d.add_value("CARD", "Cardiology", {"building": "A"})
        assert dv.key == "CARD"
        assert dv.name == "Cardiology"
        assert len(d.values) == 1

    def test_get_current_values(self):
        d = Dimension(name="Department")
        d.add_value("CARD", "Cardiology")
        d.add_value("OLD", "OldDept")
        d.values[1].is_deleted = True
        current = d.get_current_values()
        assert len(current) == 1
        assert current[0].key == "CARD"

class TestSCD2:
    def test_add_scd2_record(self):
        svc = SemanticLayerService()
        r = svc.add_scd2_record("department", "CARD", {"name": "Cardiology", "building": "A"}, datetime(2024, 1, 1))
        assert r.surrogate_key == 1
        assert r.is_current is True

    def test_get_current(self):
        svc = SemanticLayerService()
        svc.add_scd2_record("department", "CARD", {"name": "Cardiology"}, datetime(2024, 1, 1))
        current = svc.get_current_scd2("department", "CARD")
        assert current is not None
        assert current.is_current is True

    def test_scd2_versioning(self):
        svc = SemanticLayerService()
        svc.add_scd2_record("department", "CARD", {"building": "A"}, datetime(2024, 1, 1))
        svc.add_scd2_record("department", "CARD", {"building": "B"}, datetime(2024, 6, 1))
        current = svc.get_current_scd2("department", "CARD")
        assert current.attributes["building"] == "B"
        assert current.version == 2

    def test_get_historical(self):
        svc = SemanticLayerService()
        svc.add_scd2_record("department", "CARD", {"building": "A"}, datetime(2024, 1, 1))
        svc.add_scd2_record("department", "CARD", {"building": "B"}, datetime(2024, 6, 1))
        historical = svc.get_historical_scd2("department", "CARD", datetime(2024, 3, 1))
        assert historical is not None
        assert historical.attributes["building"] == "A"

    def test_get_historical_none(self):
        svc = SemanticLayerService()
        svc.add_scd2_record("department", "CARD", {"building": "A"}, datetime(2024, 1, 1))
        historical = svc.get_historical_scd2("department", "CARD", datetime(2023, 1, 1))
        assert historical is None

class TestFactTable:
    def test_create_fact_table(self):
        f = FactTable(name="Charges", physical_name="fact_charges")
        assert f.name == "Charges"

    def test_add_column(self):
        f = FactTable(name="Charges")
        c = f.add_column(name="amount", data_type="DECIMAL(18,2)", is_measure=True)
        assert c.is_measure is True
        assert len(f.columns) == 1

    def test_get_measures(self):
        f = FactTable(name="Charges")
        f.add_column(name="amount", is_measure=True)
        f.add_column(name="dept_id", is_dimension_key=True)
        f.add_column(name="charge_id", is_dimension_key=True)
        measures = f.get_measures()
        assert len(measures) == 1

    def test_get_dimension_keys(self):
        f = FactTable(name="Charges")
        f.add_column(name="amount", is_measure=True)
        f.add_column(name="dept_id", is_dimension_key=True)
        keys = f.get_dimension_keys()
        assert len(keys) == 1

class TestRelationships:
    def test_add_relationship(self):
        svc = SemanticLayerService()
        rel = svc.add_relationship(source_table="fact_charges", target_table="departments",
            join_condition="fact_charges.dept_id = departments.id")
        assert rel.source_table == "fact_charges"

    def test_find_relationships(self):
        svc = SemanticLayerService()
        svc.add_relationship(source_table="fact_charges", target_table="departments",
            join_condition="fact_charges.dept_id = departments.id")
        svc.add_relationship(source_table="fact_payments", target_table="departments",
            join_condition="fact_payments.dept_id = departments.id")
        rels = svc.find_relationships("fact_charges", "departments")
        assert len(rels) == 1

class TestAliases:
    def test_add_and_resolve(self):
        svc = SemanticLayerService()
        svc.add_alias("Department", "Division", "dimension", uuid4())
        assert svc.resolve_alias("Division") == "Department"

    def test_resolve_unknown(self):
        svc = SemanticLayerService()
        assert svc.resolve_alias("Unknown") == "Unknown"

    def test_case_insensitive(self):
        svc = SemanticLayerService()
        svc.add_alias("Department", "Facility", "dimension", uuid4())
        assert svc.resolve_alias("facility") == "Department"

class TestHierarchies:
    def test_add_hierarchy(self):
        svc = SemanticLayerService()
        dim = svc.create_dimension(name="Department")
        h = svc.add_hierarchy(dim.id, "Hospital→Dept", [
            {"level_name": "hospital", "dimension_id": str(uuid4()), "key_column": "hospital_id", "name_column": "hospital_name"},
            {"level_name": "department", "dimension_id": str(dim.id), "key_column": "dept_id", "name_column": "dept_name"},
        ])
        assert len(h.levels) == 2
        assert h.levels[0].level_name == "hospital"

class TestSemanticLayerService:
    def test_create_dimension(self):
        svc = SemanticLayerService()
        d = svc.create_dimension(name="Payer", slug="payer")
        assert svc.get_dimension(d.id) is not None

    def test_list_dimensions(self):
        svc = SemanticLayerService()
        svc.create_dimension(name="A", cardinality=Cardinality.HIGH)
        svc.create_dimension(name="B", cardinality=Cardinality.LOW)
        high = svc.list_dimensions(cardinality=Cardinality.HIGH)
        assert len(high) == 1

    def test_create_fact_table(self):
        svc = SemanticLayerService()
        f = svc.create_fact_table(name="Payments")
        assert len(svc.list_fact_tables()) == 1

    def test_add_scd2_and_query(self):
        svc = SemanticLayerService()
        svc.add_scd2_record("department", "CARD", {"name": "Cardiology", "building": "A"}, datetime(2024, 1, 1))
        svc.add_scd2_record("department", "CARD", {"name": "Cardiology", "building": "B"}, datetime(2024, 6, 1))
        current = svc.get_current_scd2("department", "CARD")
        assert current.attributes["building"] == "B"
        historical = svc.get_historical_scd2("department", "CARD", datetime(2024, 3, 1))
        assert historical.attributes["building"] == "A"
