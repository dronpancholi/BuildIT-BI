import pytest
from uuid import uuid4
from decimal import Decimal
from app.domain.forecasting import (
    ForecastingService, ForecastModelConfig, ForecastResult, MonitoringAlert,
    ChampionChallengerResult, ForecastModel, ModelStatus, DriftType, MonitoringStatus,
)


class TestForecastingService:
    def setup_method(self):
        self.service = ForecastingService()
        self.tenant_id = str(uuid4())

    def test_create_model(self):
        model = self.service.create_model(
            self.tenant_id, "Rev Forecast", ForecastModel.LINEAR_REGRESSION,
            {"intercept": 0}, {"alpha": 0.3}
        )
        assert isinstance(model, ForecastModelConfig)
        assert model.name == "Rev Forecast"
        assert model.status == ModelStatus.TRAINING

    def test_get_model(self):
        m = self.service.create_model(self.tenant_id, "M", ForecastModel.PROPHET, {}, {})
        result = self.service.get_model(self.tenant_id, m.id)
        assert result is not None

    def test_get_model_returns_none(self):
        result = self.service.get_model(self.tenant_id, uuid4())
        assert result is None

    def test_list_models(self):
        self.service.create_model(self.tenant_id, "M1", ForecastModel.ARIMA, {}, {})
        self.service.create_model(self.tenant_id, "M2", ForecastModel.PROPHET, {}, {})
        models = self.service.list_models(self.tenant_id)
        assert len(models) >= 2

    def test_list_models_filters_by_status(self):
        self.service.create_model(self.tenant_id, "M", ForecastModel.PROPHET, {}, {})
        models = self.service.list_models(self.tenant_id, status=ModelStatus.TRAINING)
        assert all(m.status == ModelStatus.TRAINING for m in models)

    def test_train_model(self):
        m = self.service.create_model(self.tenant_id, "M", ForecastModel.LINEAR_REGRESSION, {}, {})
        training_data = [{"date": f"2025-0{i+1}", "value": 100 + i * 10} for i in range(6)]
        trained = self.service.train_model(self.tenant_id, m.id, training_data, "value", "date")
        assert trained.training_metadata.get("data_points") == 6

    def test_generate_forecast(self):
        m = self.service.create_model(self.tenant_id, "M", ForecastModel.LINEAR_REGRESSION, {}, {})
        training_data = [{"date": f"2025-0{i+1}", "actual": 100 + i * 10} for i in range(6)]
        forecast = self.service.generate_forecast(
            self.tenant_id, m.id, uuid4(), "Revenue", 3, training_data, 0.95
        )
        assert isinstance(forecast, ForecastResult)
        assert len(forecast.values) == 3

    def test_evaluate_model(self):
        m = self.service.create_model(self.tenant_id, "M", ForecastModel.LINEAR_REGRESSION, {}, {})
        training_data = [{"date": f"2025-0{i+1}", "value": 100 + i * 10} for i in range(6)]
        self.service.train_model(self.tenant_id, m.id, training_data, "value", "date")
        test_data = [{"date": "2025-07", "actual": 160, "forecast": 155}]
        metrics = self.service.evaluate_model(self.tenant_id, m.id, test_data)
        assert "mape" in metrics
        assert "rmse" in metrics
        assert "mae" in metrics
        assert "r_squared" in metrics

    def test_compare_models(self):
        m1 = self.service.create_model(self.tenant_id, "M1", ForecastModel.LINEAR_REGRESSION, {}, {})
        m2 = self.service.create_model(self.tenant_id, "M2", ForecastModel.EXPONENTIAL_SMOOTHING, {}, {})
        comparison = self.service.compare_models(self.tenant_id, [m1.id, m2.id], "Revenue", [])
        assert isinstance(comparison, ChampionChallengerResult)
        assert comparison.winner in ["champion", "challenger"]

    def test_create_ensemble(self):
        m1 = self.service.create_model(self.tenant_id, "M1", ForecastModel.LINEAR_REGRESSION, {}, {})
        m2 = self.service.create_model(self.tenant_id, "M2", ForecastModel.EXPONENTIAL_SMOOTHING, {}, {})
        result = self.service.create_ensemble(self.tenant_id, [m1, m2], [0.6, 0.4], "Revenue")
        assert isinstance(result, ForecastResult)

    def test_detect_drift(self):
        m = self.service.create_model(self.tenant_id, "M", ForecastModel.LINEAR_REGRESSION, {}, {})
        reference = [{"actual": 100, "forecast": 101}] * 10
        recent = [{"actual": 100, "forecast": 120}] * 10
        alerts = self.service.detect_drift(self.tenant_id, m.id, recent, reference)
        assert isinstance(alerts, list)

    def test_promote_model(self):
        m = self.service.create_model(self.tenant_id, "M", ForecastModel.PROPHET, {}, {})
        promoted = self.service.promote_model(self.tenant_id, m.id)
        assert promoted.status == ModelStatus.VALIDATED

    def test_demote_model(self):
        m = self.service.create_model(self.tenant_id, "M", ForecastModel.PROPHET, {}, {})
        self.service.promote_model(self.tenant_id, m.id)
        demoted = self.service.demote_model(self.tenant_id, m.id)
        assert demoted.status != ModelStatus.PRODUCTION

    def test_forecast_model_enum(self):
        assert len(ForecastModel) == 6

    def test_model_status_enum(self):
        assert len(ModelStatus) == 7
