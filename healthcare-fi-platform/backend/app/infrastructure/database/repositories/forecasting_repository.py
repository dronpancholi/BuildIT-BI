"""
SQLAlchemy repositories for the Forecasting domain.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models import (
    ForecastModelModel,
    ForecastResultModel,
    ForecastMonitoringAlertModel,
)


class ForecastModelRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        tenant_id: str,
        name: str,
        model_type: str,
        parameters: Dict[str, Any],
        hyperparameters: Dict[str, Any],
        status: str = "TRAINING",
    ) -> ForecastModelModel:
        model = ForecastModelModel(
            tenant_id=tenant_id,
            name=name,
            model_type=model_type,
            parameters=parameters,
            hyperparameters=hyperparameters,
            status=status,
            training_metadata={
                "data_points": 0,
                "training_time_seconds": 0.0,
                "algorithm_version": "1.0.0",
            },
        )
        self._session.add(model)
        await self._session.flush()
        return model

    async def get_by_id(self, model_id: uuid.UUID) -> Optional[ForecastModelModel]:
        result = await self._session.execute(
            select(ForecastModelModel).where(ForecastModelModel.id == model_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_tenant(
        self, model_id: uuid.UUID, tenant_id: str
    ) -> Optional[ForecastModelModel]:
        result = await self._session.execute(
            select(ForecastModelModel).where(
                ForecastModelModel.id == model_id,
                ForecastModelModel.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_models(
        self,
        tenant_id: str,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 100,
    ) -> List[ForecastModelModel]:
        query = select(ForecastModelModel).where(
            ForecastModelModel.tenant_id == tenant_id
        )
        if status:
            query = query.where(ForecastModelModel.status == status)
        query = query.order_by(ForecastModelModel.created_at.desc()).offset(offset).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(self, tenant_id: str, status: Optional[str] = None) -> int:
        query = select(func.count()).select_from(ForecastModelModel).where(
            ForecastModelModel.tenant_id == tenant_id
        )
        if status:
            query = query.where(ForecastModelModel.status == status)
        result = await self._session.execute(query)
        return result.scalar() or 0

    async def update_status(
        self, model_id: uuid.UUID, status: str, training_metadata: Optional[Dict] = None
    ) -> Optional[ForecastModelModel]:
        model = await self.get_by_id(model_id)
        if model is None:
            return None
        model.status = status
        model.updated_at = datetime.utcnow()
        if training_metadata is not None:
            model.training_metadata = training_metadata
        await self._session.flush()
        return model

    async def update_model(
        self,
        model_id: uuid.UUID,
        status: Optional[str] = None,
        training_metadata: Optional[Dict] = None,
        model_artifact: Optional[bytes] = None,
    ) -> Optional[ForecastModelModel]:
        model = await self.get_by_id(model_id)
        if model is None:
            return None
        if status is not None:
            model.status = status
        if training_metadata is not None:
            model.training_metadata = training_metadata
        if model_artifact is not None:
            model.model_artifact = model_artifact
        model.updated_at = datetime.utcnow()
        await self._session.flush()
        return model


class ForecastResultRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        tenant_id: str,
        model_id: uuid.UUID,
        metric_id: str,
        metric_name: str,
        period: str,
        values: List[Dict],
        metrics: Dict[str, Any],
        model_name: str,
        model_type: str,
        confidence_level: float = 0.95,
    ) -> ForecastResultModel:
        result = ForecastResultModel(
            model_id=model_id,
            tenant_id=tenant_id,
            metric_id=metric_id,
            metric_name=metric_name,
            period=period,
            values=values,
            metrics=metrics,
            model_name=model_name,
            model_type=model_type,
            confidence_level=confidence_level,
        )
        self._session.add(result)
        await self._session.flush()
        return result

    async def get_by_id(self, result_id: uuid.UUID) -> Optional[ForecastResultModel]:
        q = await self._session.execute(
            select(ForecastResultModel).where(ForecastResultModel.id == result_id)
        )
        return q.scalar_one_or_none()

    async def list_by_model(
        self, model_id: uuid.UUID, tenant_id: str, offset: int = 0, limit: int = 100
    ) -> List[ForecastResultModel]:
        q = await self._session.execute(
            select(ForecastResultModel)
            .where(
                ForecastResultModel.model_id == model_id,
                ForecastResultModel.tenant_id == tenant_id,
            )
            .order_by(ForecastResultModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(q.scalars().all())

    async def list_by_tenant(
        self, tenant_id: str, offset: int = 0, limit: int = 100
    ) -> List[ForecastResultModel]:
        q = await self._session.execute(
            select(ForecastResultModel)
            .where(ForecastResultModel.tenant_id == tenant_id)
            .order_by(ForecastResultModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(q.scalars().all())


class ForecastAlertRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(
        self,
        tenant_id: str,
        model_id: uuid.UUID,
        metric_name: str,
        alert_type: str,
        severity: str,
        details: Dict[str, Any],
    ) -> ForecastMonitoringAlertModel:
        alert = ForecastMonitoringAlertModel(
            model_id=model_id,
            tenant_id=tenant_id,
            metric_name=metric_name,
            alert_type=alert_type,
            severity=severity,
            details=details,
            message=details.get("message", ""),
            drift_score=details.get("ratio") or details.get("z_score"),
        )
        self._session.add(alert)
        await self._session.flush()
        return alert

    async def create_many(
        self,
        tenant_id: str,
        model_id: uuid.UUID,
        alerts_data: List[Dict[str, Any]],
    ) -> List[ForecastMonitoringAlertModel]:
        created = []
        for a in alerts_data:
            alert = ForecastMonitoringAlertModel(
                model_id=model_id,
                tenant_id=tenant_id,
                metric_name=a.get("metric_name", ""),
                alert_type=a.get("alert_type", ""),
                severity=a.get("severity", "INFO"),
                details=a.get("details", {}),
                message=a.get("details", {}).get("message", ""),
                drift_score=a.get("details", {}).get("ratio")
                or a.get("details", {}).get("z_score"),
            )
            self._session.add(alert)
            created.append(alert)
        await self._session.flush()
        return created

    async def list_by_model(
        self, model_id: uuid.UUID, tenant_id: str, offset: int = 0, limit: int = 100
    ) -> List[ForecastMonitoringAlertModel]:
        q = await self._session.execute(
            select(ForecastMonitoringAlertModel)
            .where(
                ForecastMonitoringAlertModel.model_id == model_id,
                ForecastMonitoringAlertModel.tenant_id == tenant_id,
            )
            .order_by(ForecastMonitoringAlertModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(q.scalars().all())

    async def list_unresolved(
        self, tenant_id: str, offset: int = 0, limit: int = 100
    ) -> List[ForecastMonitoringAlertModel]:
        q = await self._session.execute(
            select(ForecastMonitoringAlertModel)
            .where(
                ForecastMonitoringAlertModel.tenant_id == tenant_id,
                ForecastMonitoringAlertModel.is_resolved == False,
            )
            .order_by(ForecastMonitoringAlertModel.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(q.scalars().all())

    async def resolve_alert(self, alert_id: uuid.UUID) -> Optional[ForecastMonitoringAlertModel]:
        q = await self._session.execute(
            select(ForecastMonitoringAlertModel).where(
                ForecastMonitoringAlertModel.id == alert_id
            )
        )
        alert = q.scalar_one_or_none()
        if alert is None:
            return None
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        await self._session.flush()
        return alert
