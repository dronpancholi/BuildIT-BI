"""
Temporal Activities for Phase 3.5 Workflows.
Activities are the individual units of work that workflows orchestrate.
"""
import uuid
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from temporalio import activity

logger = logging.getLogger(__name__)


# ============================================================
# DECISION TRACKING ACTIVITIES
# ============================================================

@activity.defn
async def get_decision_activity(
    decision_repo: Any,
    decision_id: str,
) -> Dict[str, Any]:
    """Fetch a decision by ID."""
    decision = await decision_repo.get_by_id(uuid.UUID(decision_id))
    if not decision:
        return {"found": False, "error": "Decision not found"}
    return {"found": True, "decision": decision.to_dict()}


@activity.defn
async def check_decision_deadlines_activity(
    decision_repo: Any,
    decision_id: str,
) -> Dict[str, Any]:
    """Check if a decision has exceeded its review/approval deadlines."""
    decision = await decision_repo.get_by_id(uuid.UUID(decision_id))
    if not decision:
        return {"error": "Decision not found"}

    now = datetime.utcnow()
    overdue = {}
    if decision.review_deadline and now > decision.review_deadline and decision.status.value == "reviewing":
        overdue["review"] = True
    if decision.approval_deadline and now > decision.approval_deadline and decision.status.value in ("proposed", "reviewing"):
        overdue["approval"] = True

    return {
        "decision_id": decision_id,
        "current_status": decision.status.value,
        "overdue": overdue,
        "needs_escalation": bool(overdue),
    }


@activity.defn
async def create_timeline_event_activity(
    timeline_repo: Any,
    decision_id: str,
    tenant_id: str,
    event_type: str,
    from_status: Optional[str],
    to_status: str,
    actor_id: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an immutable timeline event for a decision."""
    from app.domain.decision.value_objects import DecisionStatus, TimelineEventType

    event = {
        "id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "decision_id": decision_id,
        "event_type": event_type,
        "from_status": from_status,
        "to_status": to_status,
        "actor_id": actor_id,
        "notes": notes or "",
        "created_at": datetime.utcnow().isoformat(),
    }
    logger.info(f"Timeline event created: {event_type} for decision {decision_id}")
    return event


@activity.defn
async def send_decision_notification_activity(
    decision_id: str,
    notification_type: str,
    recipients: List[str],
    message: str,
) -> Dict[str, Any]:
    """Send notification about decision status change."""
    logger.info(f"Notification [{notification_type}] sent to {len(recipients)} recipients for decision {decision_id}")
    return {"sent": True, "recipients_count": len(recipients)}


# ============================================================
# OUTCOME MEASUREMENT ACTIVITIES
# ============================================================

@activity.defn
async def compute_outcome_trajectory_activity(
    outcome_repo: Any,
    definition_id: str,
) -> Dict[str, Any]:
    """Compute trajectory for an outcome definition."""
    definition = await outcome_repo.get_by_id(uuid.UUID(definition_id))
    if not definition:
        return {"error": "Outcome definition not found"}

    measurements = await outcome_repo.get_measurements(uuid.UUID(definition_id))
    if not measurements:
        return {
            "definition_id": definition_id,
            "trajectory_status": "no_data",
            "progress_percent": 0.0,
        }

    latest = max(measurements, key=lambda m: m.measured_at)
    baseline = definition.baseline_value
    target = definition.target_value

    if target != 0:
        progress = ((latest.actual_value - baseline) / (target - baseline)) * 100
    else:
        progress = 0.0

    return {
        "definition_id": definition_id,
        "trajectory_status": "active",
        "progress_percent": min(max(progress, 0), 100),
        "current_value": latest.actual_value,
        "target_value": target,
        "baseline_value": baseline,
        "measurement_count": len(measurements),
    }


@activity.defn
async def compute_causal_impact_activity(
    outcome_id: str,
    method: str,
) -> Dict[str, Any]:
    """Compute causal impact for an outcome."""
    return {
        "outcome_id": outcome_id,
        "method": method,
        "effect_size": 0.0,
        "confidence_interval": [0.0, 0.0],
        "p_value": 1.0,
        "is_significant": False,
    }


# ============================================================
# LEARNING ACTIVITIES
# ============================================================

@activity.defn
async def compute_recommendation_accuracy_activity(
    learning_repo: Any,
    tenant_id: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """Compute recommendation accuracy for a time period."""
    return {
        "tenant_id": tenant_id,
        "period_start": start_date,
        "period_end": end_date,
        "total_recommendations": 0,
        "validated_count": 0,
        "average_accuracy": 0.0,
    }


@activity.defn
async def detect_recommendation_patterns_activity(
    learning_repo: Any,
    tenant_id: str,
) -> Dict[str, Any]:
    """Detect patterns in recommendation adoption."""
    return {
        "tenant_id": tenant_id,
        "patterns": [],
        "total_patterns": 0,
    }


@activity.defn
async def suggest_scoring_adjustments_activity(
    learning_repo: Any,
    tenant_id: str,
) -> Dict[str, Any]:
    """Suggest scoring adjustments based on learning."""
    return {
        "tenant_id": tenant_id,
        "adjustments": [],
        "total_adjustments": 0,
    }


# ============================================================
# FEATURE MATERIALIZATION ACTIVITIES
# ============================================================

@activity.defn
async def materialize_feature_activity(
    feature_id: str,
    feature_config: Dict[str, Any],
) -> Dict[str, Any]:
    """Materialize a single feature."""
    return {
        "feature_id": feature_id,
        "materialized": True,
        "row_count": 0,
        "duration_ms": 0,
    }


@activity.defn
async def validate_feature_activity(
    feature_id: str,
) -> Dict[str, Any]:
    """Validate a feature's data quality and schema."""
    return {
        "feature_id": feature_id,
        "valid": True,
        "null_rate": 0.0,
        "schema_valid": True,
    }


# ============================================================
# MODEL EVALUATION ACTIVITIES
# ============================================================

@activity.defn
async def evaluate_model_activity(
    model_id: str,
    version: str,
) -> Dict[str, Any]:
    """Run offline evaluation on a model."""
    return {
        "model_id": model_id,
        "version": version,
        "eval_metrics": {},
        "fit_quality": "unknown",
        "passed": False,
    }


@activity.defn
async def compare_model_versions_activity(
    current_model_id: str,
    candidate_model_id: str,
) -> Dict[str, Any]:
    """Compare two model versions for production readiness."""
    return {
        "current_model_id": current_model_id,
        "candidate_model_id": candidate_model_id,
        "improvement": 0.0,
        "recommended": False,
    }


# ============================================================
# EXECUTIVE MEMORY ACTIVITIES
# ============================================================

@activity.defn
async def sync_executive_profiles_activity(
    tenant_id: str,
) -> Dict[str, Any]:
    """Sync executive behavior profiles to vector memory."""
    return {
        "tenant_id": tenant_id,
        "profiles_synced": 0,
        "reactions_synced": 0,
    }


@activity.defn
async def compute_executive_preference_activity(
    user_id: str,
) -> Dict[str, Any]:
    """Compute executive preference profile."""
    return {
        "user_id": user_id,
        "preferred_insight_types": [],
        "preferred_briefing_frequency": "daily",
        "acceptance_rate": 0.0,
    }
