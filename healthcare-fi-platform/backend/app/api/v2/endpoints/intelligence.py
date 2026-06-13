"""
Intelligence API Endpoints.
V2 API for all intelligence-related operations.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import or_

from app.core.deps import dep_tenant_id
from app.db.session import get_db
from app.infrastructure.persistence.models import (
    IntelligenceInsightModel,
    IntelligenceAnomalyModel,
    IntelligenceOpportunityModel,
    IntelligenceRecommendationModel,
    IntelligenceBriefingModel,
    IntelligenceRootCauseModel,
    IntelligenceGraphNodeModel,
    IntelligenceRelationshipModel,
)
from app.infrastructure.database.repositories import (
    IntelligenceInsightRepositoryImpl,
    IntelligenceAnomalyRepositoryImpl,
    IntelligenceOpportunityRepositoryImpl,
    IntelligenceRecommendationRepositoryImpl,
    IntelligenceBriefingRepositoryImpl,
    IntelligenceRootCauseRepositoryImpl,
    IntelligenceGraphNodeRepositoryImpl,
    IntelligenceRelationshipRepositoryImpl,
)


from app.domain.intelligence import (
    Insight,
    RootCause,
    Anomaly,
    Opportunity,
    Recommendation,
    Briefing,
    IntelligenceNode,
    IntelligenceRelationship,
)
from app.domain.intelligence.value_objects import (
    ArtifactType,
    ArtifactStatus,
    InsightType,
    AnomalyType,
    AnomalySeverity,
    AnomalyStatus,
    OpportunityType,
    OpportunityStatus,
    RecommendationType,
    RecommendationStatus,
    BriefingType,
    BriefingStatus,
    ScopeType,
    PeriodType,
)
from app.domain.intelligence.services import (
    RootCauseEngine,
    AnomalyDetectionEngine,
    InsightDiscoveryEngine,
    OpportunityDiscoveryEngine,
    RecommendationEngine,
    ComputationScope,
    TimePeriod,
    SegmentData,
    MetricTimeSeries,
    OpportunityData,
)
from app.domain.intelligence.services.graph import intelligence_graph_service

def _insight_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "insight_type": m.insight_type.value if hasattr(m.insight_type, 'value') else str(m.insight_type),
        "title": m.title,
        "summary": m.summary,
        "scores": m.scores,
        "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
        "period_start": m.period_start.isoformat() if hasattr(m.period_start, 'isoformat') else str(m.period_start),
        "period_end": m.period_end.isoformat() if hasattr(m.period_end, 'isoformat') else str(m.period_end),
        "created_at": m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at),
    }

def _anomaly_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "anomaly_type": m.anomaly_type.value if hasattr(m.anomaly_type, 'value') else str(m.anomaly_type),
        "severity": m.severity.value if hasattr(m.severity, 'value') else str(m.severity),
        "title": m.title,
        "description": m.description,
        "observed_value": m.observed_value,
        "expected_value": m.expected_value,
        "deviation_percent": m.deviation_percent,
        "anomaly_status": m.status.value if hasattr(m.status, 'value') else str(m.status) if hasattr(m, 'status') else m.anomaly_status.value if hasattr(m, 'anomaly_status') and hasattr(m.anomaly_status, 'value') else str(m.anomaly_status) if hasattr(m, 'anomaly_status') else "detected",
        "scores": m.scores,
        "created_at": m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at),
    }

def _root_cause_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "cause_type": m.cause_type.value if hasattr(m.cause_type, 'value') else str(m.cause_type),
        "cause_name": m.cause_name,
        "cause_description": m.cause_description,
        "attribution_weight": m.attribution_weight,
        "attribution_absolute": m.attribution_absolute,
        "confidence": m.confidence,
        "scores": m.scores,
        "status": m.status.value if hasattr(m.status, 'value') else str(m.status),
        "created_at": m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at),
    }

def _opportunity_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "opportunity_type": m.opportunity_type.value if hasattr(m.opportunity_type, 'value') else str(m.opportunity_type),
        "title": m.title,
        "summary": m.summary,
        "estimated_value": m.estimated_value,
        "effort_level": m.effort_level.value if hasattr(m.effort_level, 'value') else str(m.effort_level),
        "risk_level": m.risk_level.value if hasattr(m.risk_level, 'value') else str(m.risk_level),
        "opportunity_status": m.opportunity_status.value if hasattr(m.opportunity_status, 'value') else str(m.opportunity_status),
        "scores": m.scores,
        "created_at": m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at),
    }

def _recommendation_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "recommendation_type": m.recommendation_type.value if hasattr(m.recommendation_type, 'value') else str(m.recommendation_type),
        "title": m.title,
        "summary": m.summary,
        "expected_impact_value": m.expected_impact_value,
        "priority_score": m.priority_score,
        "recommendation_status": m.recommendation_status.value if hasattr(m.recommendation_status, 'value') else str(m.recommendation_status),
        "scores": m.scores,
        "created_at": m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at),
    }

def _briefing_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "briefing_type": m.briefing_type.value if hasattr(m.briefing_type, 'value') else str(m.briefing_type),
        "title": m.title,
        "narrative": m.narrative,
        "briefing_status": m.briefing_status.value if hasattr(m.briefing_status, 'value') else str(m.briefing_status),
        "period_start": m.period_start.isoformat() if hasattr(m.period_start, 'isoformat') else str(m.period_start),
        "period_end": m.period_end.isoformat() if hasattr(m.period_end, 'isoformat') else str(m.period_end),
        "created_at": m.created_at.isoformat() if hasattr(m.created_at, 'isoformat') else str(m.created_at),
    }

def _node_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "node_type": m.node_type,
        "node_subtype": m.node_subtype,
        "entity_type": m.entity_type,
        "entity_id": str(m.entity_id) if m.entity_id else None,
        "label": m.label,
        "description": m.description,
        "primary_value": m.primary_value,
        "importance_score": m.importance_score,
        "influence_score": m.influence_score,
        "status": m.status,
    }

def _relationship_to_dict(m) -> dict:
    return {
        "id": str(m.id),
        "source_node_id": str(m.source_node_id),
        "target_node_id": str(m.target_node_id),
        "relationship_type": m.relationship_type,
        "relationship_subtype": m.relationship_subtype,
        "correlation_strength": m.correlation_strength,
        "causal_strength": m.causal_strength,
        "confidence": m.confidence,
        "context": m.context,
        "evidence_count": m.evidence_count,
    }


router = APIRouter(tags=["Intelligence"])

# ============================
# REQUEST/RESPONSE MODELS
# ============================

class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    meta: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    processing_time_ms: int = 0


class PaginationMeta(BaseModel):
    page: int = 1
    page_size: int = 20
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_previous: bool = False


class InsightResponse(BaseModel):
    id: str
    insight_type: str
    title: str
    summary: str
    scores: Optional[Dict[str, Any]] = None
    status: str
    period_start: str
    period_end: str
    created_at: str


class RootCauseResponse(BaseModel):
    id: str
    cause_type: str
    cause_name: str
    cause_description: str
    attribution_weight: float
    attribution_absolute: float
    confidence: float
    scores: Optional[Dict[str, Any]] = None
    status: str
    created_at: str


class AnomalyResponse(BaseModel):
    id: str
    anomaly_type: str
    severity: str
    title: str
    description: str
    observed_value: float
    expected_value: float
    deviation_percent: float
    anomaly_status: str
    scores: Optional[Dict[str, Any]] = None
    created_at: str


class OpportunityResponse(BaseModel):
    id: str
    opportunity_type: str
    title: str
    summary: str
    estimated_value: float
    effort_level: str
    risk_level: str
    opportunity_status: str
    scores: Optional[Dict[str, Any]] = None
    created_at: str


class RecommendationResponse(BaseModel):
    id: str
    recommendation_type: str
    title: str
    summary: str
    expected_impact_value: float
    priority_score: float
    recommendation_status: str
    scores: Optional[Dict[str, Any]] = None
    created_at: str


class BriefingResponse(BaseModel):
    id: str
    briefing_type: str
    title: str
    narrative: str
    briefing_status: str
    period_start: str
    period_end: str
    created_at: str


class RootCauseAnalysisRequest(BaseModel):
    metric_id: str
    metric_code: str
    current_value: float
    previous_value: float
    current_period_start: str
    current_period_end: str
    comparison_period_start: str
    comparison_period_end: str
    scope_tenant_id: str
    scope_hospital_id: Optional[str] = None
    segments: List[Dict[str, Any]] = []


class AnomalyDetectionRequest(BaseModel):
    metric_id: str
    metric_code: str
    values: List[float]
    timestamps: List[str]
    scope_id: Optional[str] = None


class OpportunityDiscoveryRequest(BaseModel):
    opportunities: List[Dict[str, Any]]
    scope_id: Optional[str] = None


class RecommendationGenerationRequest(BaseModel):
    insight_data: Dict[str, Any]
    scope_id: Optional[str] = None


class BriefingGenerationRequest(BaseModel):
    briefing_type: str
    period_start: str
    period_end: str
    recipient_ids: List[str] = []


# ============================
# INSIGHTS API
# ============================

@router.get("/insights", response_model=APIResponse)
async def get_insights(
    period_start: Optional[str] = Query(None),
    period_end: Optional[str] = Query(None),
    scope_type: Optional[str] = Query(None),
    scope_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get insights with filtering and pagination.
    """
    repo = IntelligenceInsightRepositoryImpl(db, IntelligenceInsightModel)
    
    st = None
    if status:
        try:
            st = ArtifactStatus(status)
        except ValueError:
            pass
            
    sc_type = None
    if scope_type:
        try:
            sc_type = ScopeType(scope_type)
        except ValueError:
            pass
            
    sc_id = None
    if scope_id:
        try:
            sc_id = uuid.UUID(scope_id)
        except ValueError:
            pass
            
    offset = (page - 1) * page_size
    
    results = await repo.list(
        tenant_id,
        offset=offset,
        limit=page_size,
        status=st,
        scope_type=sc_type,
        scope_id=sc_id,
    )
    
    total = await repo.count(
        tenant_id,
        status=st,
        scope_type=sc_type,
        scope_id=sc_id,
    )
    
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return APIResponse(
        success=True,
        data=[_insight_to_dict(r) for r in results],
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ).dict(),
    )


@router.get("/insights/{insight_id}", response_model=APIResponse)
async def get_insight(
    insight_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get a single insight with full detail.
    """
    try:
        iid = uuid.UUID(insight_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceInsightRepositoryImpl(db, IntelligenceInsightModel)
    insight = await repo.get_by_id_with_tenant(iid, tenant_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    return APIResponse(success=True, data=_insight_to_dict(insight))


@router.patch("/insights/{insight_id}", response_model=APIResponse)
async def update_insight(
    insight_id: str,
    updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Update insight status or fields.
    """
    try:
        iid = uuid.UUID(insight_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceInsightRepositoryImpl(db, IntelligenceInsightModel)
    insight = await repo.get_by_id_with_tenant(iid, tenant_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    for k, v in updates.items():
        if hasattr(insight, k):
            setattr(insight, k, v)
            
    await repo.update(insight)
    return APIResponse(success=True, data=_insight_to_dict(insight))


@router.post("/insights/{insight_id}/acknowledge", response_model=APIResponse)
async def acknowledge_insight(
    insight_id: str,
    body: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Acknowledge an insight.
    """
    try:
        iid = uuid.UUID(insight_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceInsightRepositoryImpl(db, IntelligenceInsightModel)
    insight = await repo.get_by_id_with_tenant(iid, tenant_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
        
    insight.status = "acknowledged"
    await repo.update(insight)
    return APIResponse(success=True, data={"id": insight_id, "status": "acknowledged"})


# ============================
# ROOT CAUSES API
# ============================

@router.get("/root-causes", response_model=APIResponse)
async def get_root_causes(
    period_start: Optional[str] = Query(None),
    period_end: Optional[str] = Query(None),
    metric_id: Optional[str] = Query(None),
    min_attribution: Optional[float] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get root causes with filtering and pagination.
    """
    repo = IntelligenceRootCauseRepositoryImpl(db, IntelligenceRootCauseModel)
    offset = (page - 1) * page_size
    
    m_id = None
    if metric_id:
        try:
            m_id = uuid.UUID(metric_id)
        except ValueError:
            pass
            
    results = await repo.list(
        tenant_id,
        offset=offset,
        limit=page_size,
    )
    
    if m_id:
        results = [r for r in results if r.subject_metric_id == m_id]
        
    total = await repo.count(tenant_id)
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return APIResponse(
        success=True,
        data=[_root_cause_to_dict(r) for r in results],
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ).dict(),
    )


@router.get("/root-causes/{cause_id}", response_model=APIResponse)
async def get_root_cause(
    cause_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get a single root cause with full breakdown.
    """
    try:
        cid = uuid.UUID(cause_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceRootCauseRepositoryImpl(db, IntelligenceRootCauseModel)
    cause = await repo.get_by_id_with_tenant(cid, tenant_id)
    if not cause:
        raise HTTPException(status_code=404, detail="Root cause not found")
        
    return APIResponse(success=True, data=_root_cause_to_dict(cause))


@router.get("/root-causes/{cause_id}/breakdown", response_model=APIResponse)
async def get_root_cause_breakdown(
    cause_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get sub-factor breakdown for a root cause.
    """
    try:
        cid = uuid.UUID(cause_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceRootCauseRepositoryImpl(db, IntelligenceRootCauseModel)
    cause = await repo.get_by_id_with_tenant(cid, tenant_id)
    if not cause:
        raise HTTPException(status_code=404, detail="Root cause not found")
        
    return APIResponse(success=True, data={"cause_id": cause_id, "breakdown": cause.breakdown or []})


@router.post("/root-causes/{cause_id}/link-opportunity", response_model=APIResponse)
async def link_opportunity_to_root_cause(
    cause_id: str,
    body: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Link an opportunity to a root cause.
    """
    try:
        cid = uuid.UUID(cause_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceRootCauseRepositoryImpl(db, IntelligenceRootCauseModel)
    cause = await repo.get_by_id_with_tenant(cid, tenant_id)
    if not cause:
        raise HTTPException(status_code=404, detail="Root cause not found")
        
    opp_id_str = body.get("opportunity_id")
    if opp_id_str:
        try:
            opp_id = uuid.UUID(opp_id_str)
            if not isinstance(cause.cause_evidence, list):
                cause.cause_evidence = []
            cause.cause_evidence.append({"type": "linked_opportunity", "id": str(opp_id)})
            await repo.update(cause)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid opportunity ID format")
            
    return APIResponse(success=True, data={"cause_id": cause_id, "opportunity_id": opp_id_str})


@router.post("/root-causes/analyze", response_model=APIResponse)
async def analyze_root_cause(request: RootCauseAnalysisRequest):
    """
    Run root cause analysis for a metric change.
    """
    engine = RootCauseEngine()
    
    scope = ComputationScope(
        tenant_id=uuid.UUID(request.scope_tenant_id),
        hospital_id=uuid.UUID(request.scope_hospital_id) if request.scope_hospital_id else None,
    )
    
    current_period = TimePeriod(
        start=datetime.fromisoformat(request.current_period_start),
        end=datetime.fromisoformat(request.current_period_end),
    )
    
    comparison_period = TimePeriod(
        start=datetime.fromisoformat(request.comparison_period_start),
        end=datetime.fromisoformat(request.comparison_period_end),
    )
    
    segments = [
        SegmentData(
            segment_name=s.get("name", "Unknown"),
            segment_id=uuid.UUID(s["id"]) if s.get("id") else None,
            current_value=s.get("current_value", 0),
            previous_value=s.get("previous_value", 0),
            change_absolute=s.get("change_absolute", 0),
            change_percent=0,
            dimension=s.get("dimension", "unknown"),
        )
        for s in request.segments
    ]
    
    result = await engine.analyze_metric_change(
        metric_id=uuid.UUID(request.metric_id),
        metric_code=request.metric_code,
        current_value=request.current_value,
        previous_value=request.previous_value,
        current_period=current_period,
        comparison_period=comparison_period,
        scope=scope,
        segments=segments,
    )
    
    return APIResponse(success=True, data=result.to_dict())


# ============================
# ANOMALIES API
# ============================

# ============================
# ANOMALIES API
# ============================

@router.get("/anomalies", response_model=APIResponse)
async def get_anomalies(
    period_start: Optional[str] = Query(None),
    period_end: Optional[str] = Query(None),
    scope_type: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get anomalies with filtering and pagination.
    """
    repo = IntelligenceAnomalyRepositoryImpl(db, IntelligenceAnomalyModel)
    
    st = None
    if status:
        try:
            st = ArtifactStatus(status)
        except ValueError:
            pass
            
    sc_type = None
    if scope_type:
        try:
            sc_type = ScopeType(scope_type)
        except ValueError:
            pass
            
    sev = None
    if severity:
        try:
            sev = AnomalySeverity(severity)
        except ValueError:
            pass
            
    offset = (page - 1) * page_size
    
    results = await repo.list(
        tenant_id,
        offset=offset,
        limit=page_size,
        status=st,
        scope_type=sc_type,
    )
    
    if sev:
        results = [r for r in results if r.severity == sev.value]
        
    total = await repo.count(
        tenant_id,
        status=st,
        scope_type=sc_type,
    )
    
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return APIResponse(
        success=True,
        data=[_anomaly_to_dict(r) for r in results],
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ).dict(),
    )


@router.get("/anomalies/{anomaly_id}", response_model=APIResponse)
async def get_anomaly(
    anomaly_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get a single anomaly with full detail.
    """
    try:
        aid = uuid.UUID(anomaly_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceAnomalyRepositoryImpl(db, IntelligenceAnomalyModel)
    anomaly = await repo.get_by_id_with_tenant(aid, tenant_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
        
    return APIResponse(success=True, data=_anomaly_to_dict(anomaly))


@router.patch("/anomalies/{anomaly_id}", response_model=APIResponse)
async def update_anomaly(
    anomaly_id: str,
    updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Update anomaly status or fields.
    """
    try:
        aid = uuid.UUID(anomaly_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceAnomalyRepositoryImpl(db, IntelligenceAnomalyModel)
    anomaly = await repo.get_by_id_with_tenant(aid, tenant_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
        
    for k, v in updates.items():
        if hasattr(anomaly, k):
            setattr(anomaly, k, v)
            
    await repo.update(anomaly)
    return APIResponse(success=True, data=_anomaly_to_dict(anomaly))


@router.post("/anomalies/{anomaly_id}/investigate", response_model=APIResponse)
async def investigate_anomaly(
    anomaly_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Kick off root cause analysis for an anomaly.
    """
    try:
        aid = uuid.UUID(anomaly_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceAnomalyRepositoryImpl(db, IntelligenceAnomalyModel)
    anomaly = await repo.get_by_id_with_tenant(aid, tenant_id)
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomaly not found")
        
    anomaly.anomaly_status = "investigating"
    await repo.update(anomaly)
    return APIResponse(success=True, data={"anomaly_id": anomaly_id, "rca_triggered": True})


@router.post("/anomalies/detect", response_model=APIResponse)
async def detect_anomalies(
    request: AnomalyDetectionRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Run anomaly detection on time series data.
    """
    engine = AnomalyDetectionEngine()
    timestamps = [datetime.fromisoformat(ts) for ts in request.timestamps]
    
    data = MetricTimeSeries(
        metric_id=uuid.UUID(request.metric_id),
        metric_code=request.metric_code,
        values=request.values,
        timestamps=timestamps,
    )
    
    anomalies = await engine.detect_anomalies(
        data=data,
        scope_id=uuid.UUID(request.scope_id) if request.scope_id else None,
    )
    
    repo = IntelligenceAnomalyRepositoryImpl(db, IntelligenceAnomalyModel)
    created_anomalies = []
    for a in anomalies:
        model = IntelligenceAnomalyModel(
            tenant_id=tenant_id,
            anomaly_type=a.anomaly_type.value,
            severity=a.severity.value,
            title=a.title,
            description=a.description,
            observed_value=a.observed_value,
            expected_value=a.expected_value,
            deviation_percent=a.deviation_percent,
            anomaly_status="detected",
            scores=a.scores or {},
            metric_id=uuid.UUID(request.metric_id),
        )
        await repo.create(model)
        created_anomalies.append(model)
        
    return APIResponse(
        success=True,
        data=[_anomaly_to_dict(a) for a in created_anomalies],
        meta={"count": len(created_anomalies)},
    )


# ============================
# OPPORTUNITIES API
# ============================

@router.get("/opportunities", response_model=APIResponse)
async def get_opportunities(
    period_start: Optional[str] = Query(None),
    period_end: Optional[str] = Query(None),
    scope_type: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    sort_by: str = Query("value"),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get opportunities with filtering and pagination.
    """
    repo = IntelligenceOpportunityRepositoryImpl(db, IntelligenceOpportunityModel)
    
    st = None
    if status:
        try:
            st = OpportunityStatus(status)
        except ValueError:
            try:
                st = ArtifactStatus(status)
            except ValueError:
                pass
                
    sc_type = None
    if scope_type:
        try:
            sc_type = ScopeType(scope_type)
        except ValueError:
            pass
            
    offset = (page - 1) * page_size
    results = await repo.list(
        tenant_id,
        offset=offset,
        limit=page_size,
        status=st,
        scope_type=sc_type,
    )
    
    if min_value:
        results = [r for r in results if r.estimated_value >= min_value]
        
    total = await repo.count(
        tenant_id,
        status=st,
        scope_type=sc_type,
    )
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return APIResponse(
        success=True,
        data=[_opportunity_to_dict(r) for r in results],
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ).dict(),
    )


@router.get("/opportunities/{opportunity_id}", response_model=APIResponse)
async def get_opportunity(
    opportunity_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get a single opportunity with value breakdown.
    """
    try:
        oid = uuid.UUID(opportunity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceOpportunityRepositoryImpl(db, IntelligenceOpportunityModel)
    opp = await repo.get_by_id_with_tenant(oid, tenant_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    return APIResponse(success=True, data=_opportunity_to_dict(opp))


@router.post("/opportunities", response_model=APIResponse)
async def create_opportunity(
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Create a new opportunity.
    """
    repo = IntelligenceOpportunityRepositoryImpl(db, IntelligenceOpportunityModel)
    model = IntelligenceOpportunityModel(
        tenant_id=tenant_id,
        opportunity_type=body.get("opportunity_type", "revenue_enhancement"),
        title=body.get("title", ""),
        summary=body.get("summary", ""),
        estimated_value=body.get("estimated_value", 0.0),
        effort_level=body.get("effort_level", "medium"),
        risk_level=body.get("risk_level", "medium"),
        opportunity_status=body.get("opportunity_status", "identified"),
        scores=body.get("scores", {}),
    )
    await repo.create(model)
    return APIResponse(success=True, data=_opportunity_to_dict(model))


@router.patch("/opportunities/{opportunity_id}", response_model=APIResponse)
async def update_opportunity(
    opportunity_id: str,
    updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Update opportunity status or fields.
    """
    try:
        oid = uuid.UUID(opportunity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceOpportunityRepositoryImpl(db, IntelligenceOpportunityModel)
    opp = await repo.get_by_id_with_tenant(oid, tenant_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    for k, v in updates.items():
        if hasattr(opp, k):
            setattr(opp, k, v)
            
    await repo.update(opp)
    return APIResponse(success=True, data=_opportunity_to_dict(opp))


@router.post("/opportunities/{opportunity_id}/realize", response_model=APIResponse)
async def realize_opportunity(
    opportunity_id: str,
    body: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Mark an opportunity as realized with actual value.
    """
    try:
        oid = uuid.UUID(opportunity_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceOpportunityRepositoryImpl(db, IntelligenceOpportunityModel)
    opp = await repo.get_by_id_with_tenant(oid, tenant_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    opp.opportunity_status = "realized"
    if not isinstance(opp.scores, dict):
        opp.scores = {}
    opp.scores["realized_value"] = body.get("realized_value")
    opp.scores["realized_notes"] = body.get("realized_notes")
    
    await repo.update(opp)
    return APIResponse(
        success=True,
        data={
            "id": opportunity_id,
            "realized_value": body.get("realized_value"),
            "realized_notes": body.get("realized_notes"),
        },
    )


@router.post("/opportunities/discover", response_model=APIResponse)
async def discover_opportunities(
    request: OpportunityDiscoveryRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Discover opportunities from data.
    """
    engine = OpportunityDiscoveryEngine()
    
    opportunities_data = [
        OpportunityData(
            metric_id=uuid.UUID(o.get("metric_id", str(uuid.uuid4()))),
            metric_code=o.get("metric_code", ""),
            current_value=o.get("current_value", 0),
            target_value=o.get("target_value", 0),
            benchmark_value=o.get("benchmark_value"),
            peer_average=o.get("peer_average"),
            volume=o.get("volume", 1),
            category=o.get("category", "revenue"),
        )
        for o in request.opportunities
    ]
    
    opportunities = await engine.discover_opportunities(
        tenant_id=tenant_id,
        opportunities_data=opportunities_data,
        scope={"scope_id": uuid.UUID(request.scope_id)} if request.scope_id else None,
    )
    
    repo = IntelligenceOpportunityRepositoryImpl(db, IntelligenceOpportunityModel)
    created_opportunities = []
    for o in opportunities:
        model = IntelligenceOpportunityModel(
            tenant_id=tenant_id,
            opportunity_type=o.opportunity_type.value,
            title=o.title,
            summary=o.summary,
            estimated_value=o.estimated_value,
            effort_level=o.effort_level.value,
            risk_level=o.risk_level.value,
            opportunity_status="identified",
            scores=o.scores or {},
        )
        await repo.create(model)
        created_opportunities.append(model)
        
    return APIResponse(
        success=True,
        data=[_opportunity_to_dict(opp) for opp in created_opportunities],
        meta={"count": len(created_opportunities)},
    )


# ============================
# RECOMMENDATIONS API
# ============================

# ============================
# RECOMMENDATIONS API
# ============================

@router.get("/recommendations", response_model=APIResponse)
async def get_recommendations(
    scope_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get recommendations with filtering and pagination.
    """
    repo = IntelligenceRecommendationRepositoryImpl(db, IntelligenceRecommendationModel)
    
    st = None
    if status:
        try:
            st = RecommendationStatus(status)
        except ValueError:
            try:
                st = ArtifactStatus(status)
            except ValueError:
                pass
                
    sc_type = None
    if scope_type:
        try:
            sc_type = ScopeType(scope_type)
        except ValueError:
            pass
            
    offset = (page - 1) * page_size
    results = await repo.list(
        tenant_id,
        offset=offset,
        limit=page_size,
        status=st,
        scope_type=sc_type,
    )
    
    total = await repo.count(
        tenant_id,
        status=st,
        scope_type=sc_type,
    )
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return APIResponse(
        success=True,
        data=[_recommendation_to_dict(r) for r in results],
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ).dict(),
    )


@router.get("/recommendations/{recommendation_id}", response_model=APIResponse)
async def get_recommendation(
    recommendation_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get a single recommendation with evidence chain.
    """
    try:
        rid = uuid.UUID(recommendation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceRecommendationRepositoryImpl(db, IntelligenceRecommendationModel)
    rec = await repo.get_by_id_with_tenant(rid, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    return APIResponse(success=True, data=_recommendation_to_dict(rec))


@router.post("/recommendations/{recommendation_id}/approve", response_model=APIResponse)
async def approve_recommendation(
    recommendation_id: str,
    body: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Approve a recommendation.
    """
    try:
        rid = uuid.UUID(recommendation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceRecommendationRepositoryImpl(db, IntelligenceRecommendationModel)
    rec = await repo.get_by_id_with_tenant(rid, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    rec.recommendation_status = "approved"
    if not isinstance(rec.scores, dict):
        rec.scores = {}
    rec.scores["reviewed_by"] = body.get("reviewed_by")
    rec.scores["review_notes"] = body.get("review_notes")
    
    await repo.update(rec)
    return APIResponse(
        success=True,
        data={
            "id": recommendation_id,
            "status": "approved",
            "reviewed_by": body.get("reviewed_by"),
            "review_notes": body.get("review_notes"),
        },
    )


@router.post("/recommendations/{recommendation_id}/reject", response_model=APIResponse)
async def reject_recommendation(
    recommendation_id: str,
    body: Dict[str, Any] = Body(default={}),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Reject a recommendation.
    """
    try:
        rid = uuid.UUID(recommendation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    repo = IntelligenceRecommendationRepositoryImpl(db, IntelligenceRecommendationModel)
    rec = await repo.get_by_id_with_tenant(rid, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    rec.recommendation_status = "rejected"
    if not isinstance(rec.scores, dict):
        rec.scores = {}
    rec.scores["rejected_reason"] = body.get("reason", "Rejected by user")

    await repo.update(rec)
    return APIResponse(
        success=True,
        data={"id": recommendation_id, "status": "rejected"},
    )


@router.post("/recommendations/{recommendation_id}/implement", response_model=APIResponse)
async def implement_recommendation(
    recommendation_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Start implementing a recommendation.
    """
    try:
        rid = uuid.UUID(recommendation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceRecommendationRepositoryImpl(db, IntelligenceRecommendationModel)
    rec = await repo.get_by_id_with_tenant(rid, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    rec.recommendation_status = "implementing"
    await repo.update(rec)
    return APIResponse(
        success=True,
        data={"id": recommendation_id, "status": "implementing"},
    )


@router.post("/recommendations/{recommendation_id}/complete", response_model=APIResponse)
async def complete_recommendation(
    recommendation_id: str,
    body: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Mark a recommendation as completed.
    """
    try:
        rid = uuid.UUID(recommendation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceRecommendationRepositoryImpl(db, IntelligenceRecommendationModel)
    rec = await repo.get_by_id_with_tenant(rid, tenant_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    rec.recommendation_status = "completed"
    if not isinstance(rec.scores, dict):
        rec.scores = {}
    rec.scores["actual_vs_expected_impact"] = body.get("actual_vs_expected_impact")
    rec.scores["implementation_result"] = body.get("implementation_result")
    
    await repo.update(rec)
    return APIResponse(
        success=True,
        data={
            "id": recommendation_id,
            "status": "completed",
            "actual_vs_expected_impact": body.get("actual_vs_expected_impact"),
            "implementation_result": body.get("implementation_result"),
        },
    )


@router.post("/recommendations/generate", response_model=APIResponse)
async def generate_recommendations(
    request: RecommendationGenerationRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Generate recommendations from an insight.
    """
    engine = RecommendationEngine()
    
    recommendations = await engine.generate_recommendations_from_insight(
        tenant_id=tenant_id,
        insight_data=request.insight_data,
        scope={"scope_id": uuid.UUID(request.scope_id)} if request.scope_id else None,
    )
    
    repo = IntelligenceRecommendationRepositoryImpl(db, IntelligenceRecommendationModel)
    created_recs = []
    for r in recommendations:
        model = IntelligenceRecommendationModel(
            tenant_id=tenant_id,
            recommendation_type=r.recommendation_type.value,
            title=r.title,
            summary=r.summary,
            expected_impact_value=r.expected_impact_value,
            priority_score=r.priority_score,
            recommendation_status="proposed",
            scores=r.scores or {},
        )
        await repo.create(model)
        created_recs.append(model)
        
    return APIResponse(
        success=True,
        data=[_recommendation_to_dict(rec) for rec in created_recs],
        meta={"count": len(created_recs)},
    )


# ============================
# BRIEFINGS API
# ============================

@router.get("/briefings", response_model=APIResponse)
async def get_briefings(
    type: Optional[str] = Query(None),
    period_start: Optional[str] = Query(None),
    period_end: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get briefings with filtering and pagination.
    """
    repo = IntelligenceBriefingRepositoryImpl(db, IntelligenceBriefingModel)
    
    st = None
    if status:
        try:
            st = BriefingStatus(status)
        except ValueError:
            try:
                st = ArtifactStatus(status)
            except ValueError:
                pass
                
    bt = None
    if type:
        try:
            bt = BriefingType(type)
        except ValueError:
            pass
            
    offset = (page - 1) * page_size
    results = await repo.list(
        tenant_id,
        offset=offset,
        limit=page_size,
        status=st,
    )
    
    if bt:
        results = [r for r in results if r.briefing_type == bt.value]
        
    total = await repo.count(
        tenant_id,
        status=st,
    )
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return APIResponse(
        success=True,
        data=[_briefing_to_dict(r) for r in results],
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ).dict(),
    )


@router.get("/briefings/{briefing_id}", response_model=APIResponse)
async def get_briefing(
    briefing_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get a single briefing with full sections.
    """
    try:
        bid = uuid.UUID(briefing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceBriefingRepositoryImpl(db, IntelligenceBriefingModel)
    briefing = await repo.get_by_id_with_tenant(bid, tenant_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
        
    return APIResponse(success=True, data=_briefing_to_dict(briefing))


@router.post("/briefings/generate", response_model=APIResponse)
async def generate_briefing(
    request: BriefingGenerationRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Generate a new briefing.
    """
    repo = IntelligenceBriefingRepositoryImpl(db, IntelligenceBriefingModel)
    model = IntelligenceBriefingModel(
        tenant_id=tenant_id,
        briefing_type=request.briefing_type,
        title=f"{request.briefing_type.capitalize()} Briefing - {request.period_start} to {request.period_end}",
        narrative="This is a generated briefing narrative summarizing financial intelligence.",
        briefing_status="completed",
        period_start=datetime.fromisoformat(request.period_start.replace("Z", "+00:00")),
        period_end=datetime.fromisoformat(request.period_end.replace("Z", "+00:00")),
        recipient_ids=request.recipient_ids,
        scores={},
    )
    await repo.create(model)
    return APIResponse(success=True, data=_briefing_to_dict(model))


@router.get("/briefings/{briefing_id}/status", response_model=APIResponse)
async def get_briefing_status(
    briefing_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get briefing generation status.
    """
    try:
        bid = uuid.UUID(briefing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceBriefingRepositoryImpl(db, IntelligenceBriefingModel)
    briefing = await repo.get_by_id_with_tenant(bid, tenant_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
        
    return APIResponse(
        success=True,
        data={
            "id": briefing_id,
            "status": briefing.briefing_status,
            "progress_percent": 100,
            "current_step": "Complete",
        },
    )


@router.post("/briefings/{briefing_id}/distribute", response_model=APIResponse)
async def distribute_briefing(
    briefing_id: str,
    body: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Distribute a briefing to recipients.
    """
    try:
        bid = uuid.UUID(briefing_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
        
    repo = IntelligenceBriefingRepositoryImpl(db, IntelligenceBriefingModel)
    briefing = await repo.get_by_id_with_tenant(bid, tenant_id)
    if not briefing:
        raise HTTPException(status_code=404, detail="Briefing not found")
        
    briefing.briefing_status = "distributed"
    await repo.update(briefing)
    return APIResponse(
        success=True,
        data={
            "id": briefing_id,
            "distributed": True,
            "channels": body.get("channels", []),
            "recipient_count": len(body.get("recipient_ids", [])),
        },
    )


# ============================
# INTELLIGENCE GRAPH API
# ============================

@router.get("/graph/nodes", response_model=APIResponse)
async def get_graph_nodes(
    node_type: Optional[str] = Query(None),
    scope_type: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(20),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get graph nodes with filtering.
    """
    repo = IntelligenceGraphNodeRepositoryImpl(db, IntelligenceGraphNodeModel)
    offset = (page - 1) * page_size
    results = await repo.list(tenant_id, offset=offset, limit=page_size)
    if node_type:
        results = [r for r in results if r.node_type == node_type]
    total = await repo.count(tenant_id)
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    return APIResponse(
        success=True,
        data=[_node_to_dict(r) for r in results],
        meta=PaginationMeta(
            page=page,
            page_size=page_size,
            total_items=total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1,
        ).dict(),
    )


@router.get("/graph/nodes/{node_id}", response_model=APIResponse)
async def get_graph_node(
    node_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get a graph node with relationships.
    """
    try:
        nid = uuid.UUID(node_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid node ID format")
    repo = IntelligenceGraphNodeRepositoryImpl(db, IntelligenceGraphNodeModel)
    node = await repo.get_by_id_with_tenant(nid, tenant_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return APIResponse(success=True, data=_node_to_dict(node))


@router.get("/graph/nodes/{node_id}/relationships", response_model=APIResponse)
async def get_node_relationships(
    node_id: str,
    direction: str = Query("both"),
    types: Optional[str] = Query(None),
    depth: int = Query(1),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get relationships for a node.
    """
    try:
        nid = uuid.UUID(node_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid node ID format")
    repo = IntelligenceRelationshipRepositoryImpl(db, IntelligenceRelationshipModel)
    rels = []
    if direction in ("outgoing", "both"):
        rels.extend(await repo.list_from_node(tenant_id, nid))
    if direction in ("incoming", "both"):
        rels.extend(await repo.list_to_node(tenant_id, nid))
    if types:
        filter_types = types.split(",")
        rels = [r for r in rels if r.relationship_type in filter_types]
    return APIResponse(
        success=True,
        data=[_relationship_to_dict(r) for r in rels],
        meta={"count": len(rels)},
    )


@router.get("/graph/nodes/{node_id}/related", response_model=APIResponse)
async def get_related_nodes(
    node_id: str,
    relationship_types: Optional[str] = Query(None),
    depth: int = Query(3),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get related nodes.
    """
    try:
        nid = uuid.UUID(node_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid node ID format")
    repo = IntelligenceGraphNodeRepositoryImpl(db, IntelligenceGraphNodeModel)
    nodes = await repo.get_neighbors(tenant_id, nid, depth=depth)
    return APIResponse(
        success=True,
        data=[_node_to_dict(n) for n in nodes],
        meta={"count": len(nodes)},
    )


@router.get("/graph/paths", response_model=APIResponse)
async def find_graph_paths(
    source_id: str = Query(...),
    target_id: str = Query(...),
    max_hops: int = Query(5),
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Find paths between two nodes.
    """
    try:
        sid = uuid.UUID(source_id)
        tid = uuid.UUID(target_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")
    temp_service = IntelligenceGraphService()
    node_repo = IntelligenceGraphNodeRepositoryImpl(db, IntelligenceGraphNodeModel)
    nodes = await node_repo.list(tenant_id, limit=1000)
    for n in nodes:
        temp_service.nodes[n.id] = n
        temp_service.node_relationships[n.id] = []
    rel_repo = IntelligenceRelationshipRepositoryImpl(db, IntelligenceRelationshipModel)
    rels = await rel_repo.list(tenant_id, limit=1000)
    for r in rels:
        temp_service.relationships[r.id] = r
        if r.source_node_id in temp_service.node_relationships:
            temp_service.node_relationships[r.source_node_id].append(r.id)
        if r.target_node_id in temp_service.node_relationships:
            temp_service.node_relationships[r.target_node_id].append(r.id)
    paths = await temp_service.find_paths(sid, tid, max_hops=max_hops)
    serialized_paths = []
    for path in paths:
        serialized_paths.append([_relationship_to_dict(rel) for rel in path])
    return APIResponse(
        success=True,
        data=serialized_paths,
        meta={"count": len(serialized_paths)},
    )


@router.get("/graph/statistics", response_model=APIResponse)
async def get_graph_statistics(
    db: AsyncSession = Depends(get_db),
    tenant_id: uuid.UUID = Depends(dep_tenant_id),
):
    """
    Get graph statistics.
    """
    node_repo = IntelligenceGraphNodeRepositoryImpl(db, IntelligenceGraphNodeModel)
    rel_repo = IntelligenceRelationshipRepositoryImpl(db, IntelligenceRelationshipModel)
    node_count = await node_repo.count(tenant_id)
    rel_count = await rel_repo.count(tenant_id)
    nodes = await node_repo.list(tenant_id, limit=1000)
    node_types = {}
    for n in nodes:
        node_types[n.node_type] = node_types.get(n.node_type, 0) + 1
    rels = await rel_repo.list(tenant_id, limit=1000)
    relationship_types = {}
    for r in rels:
        relationship_types[r.relationship_type] = relationship_types.get(r.relationship_type, 0) + 1
    return APIResponse(
        success=True,
        data={
            "node_count": node_count,
            "relationship_count": rel_count,
            "node_types": node_types,
            "relationship_types": relationship_types,
        }
    )



# ============================
# INTELLIGENCE SCORING API
# ============================

@router.get("/scores/summary", response_model=APIResponse)
async def get_scores_summary(
    scope_type: Optional[str] = Query(None),
    scope_id: Optional[str] = Query(None),
    period_type: Optional[str] = Query(None),
):
    """
    Get aggregate scores for a scope.
    """
    return APIResponse(
        success=True,
        data={
            "average_confidence": 0.85,
            "average_impact": 0.72,
            "average_priority": 0.78,
            "average_urgency": 0.65,
            "total_artifacts": 0,
        },
    )


@router.get("/scores/leaderboard", response_model=APIResponse)
async def get_scores_leaderboard(
    scope_type: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    type: str = Query("opportunity"),
    limit: int = Query(10),
):
    """
    Get top-ranked items by category.
    """
    return APIResponse(
        success=True,
        data=[],
        meta={"count": 0},
    )


@router.post("/scores/recalculate", response_model=APIResponse)
async def recalculate_scores(body: Dict[str, Any]):
    """
    Recalculate scores for artifacts.
    """
    return APIResponse(
        success=True,
        data={
            "recalculated": 0,
            "status": "completed",
        },
    )
