"""
Temporal Workflow Definitions (SDK) for Phase 3.5.
These are the actual Temporal workflow definitions that orchestrate activities.
"""
import uuid
from datetime import timedelta
from typing import Dict, Any, List, Optional

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.infrastructure.temporal.activities import (
        get_decision_activity,
        check_decision_deadlines_activity,
        create_timeline_event_activity,
        send_decision_notification_activity,
        compute_outcome_trajectory_activity,
        compute_causal_impact_activity,
        compute_recommendation_accuracy_activity,
        detect_recommendation_patterns_activity,
        suggest_scoring_adjustments_activity,
        materialize_feature_activity,
        validate_feature_activity,
        evaluate_model_activity,
        compare_model_versions_activity,
        sync_executive_profiles_activity,
        compute_executive_preference_activity,
    )


# ============================================================
# WORKFLOW 1: Decision Tracking Workflow
# ============================================================

@workflow.defn
class DecisionTrackingWorkflow:
    """
    Monitors a decision through its full lifecycle.
    Triggers at: PROPOSED
    Completes at: ARCHIVED
    """

    @workflow.run
    async def run(self, decision_id: str, tenant_id: str) -> Dict[str, Any]:
        # Fetch the decision
        result = await workflow.execute_activity(
            get_decision_activity,
            args=[decision_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        if not result.get("found"):
            return {"error": result.get("error", "Decision not found")}

        decision = result["decision"]

        # Check deadlines
        deadline_check = await workflow.execute_activity(
            check_decision_deadlines_activity,
            args=[decision_id],
            start_to_close_timeout=timedelta(seconds=30),
        )

        if deadline_check.get("needs_escalation"):
            await workflow.execute_activity(
                send_decision_notification_activity,
                args=[
                    decision_id,
                    "deadline_escalation",
                    [],
                    f"Decision {decision['title']} has exceeded deadlines",
                ],
                start_to_close_timeout=timedelta(seconds=30),
            )

        return {
            "decision_id": decision_id,
            "status": decision["status"],
            "deadline_check": deadline_check,
        }


# ============================================================
# WORKFLOW 2: Outcome Measurement Workflow
# ============================================================

@workflow.defn
class OutcomeMeasurementWorkflow:
    """
    Tracks an outcome definition and collects measurements over time.
    Triggers at: COMPLETED decision
    """

    @workflow.run
    async def run(self, outcome_def_id: str, tenant_id: str) -> Dict[str, Any]:
        trajectory = await workflow.execute_activity(
            compute_outcome_trajectory_activity,
            args=[outcome_def_id],
            start_to_close_timeout=timedelta(seconds=60),
        )

        return {
            "outcome_def_id": outcome_def_id,
            "trajectory": trajectory,
        }


# ============================================================
# WORKFLOW 3: Learning Workflow
# ============================================================

@workflow.defn
class LearningWorkflow:
    """
    Periodically computes learning metrics and adjusts scoring.
    Schedule: Daily at 2 AM
    """

    @workflow.run
    async def run(self, tenant_id: str) -> Dict[str, Any]:
        accuracy = await workflow.execute_activity(
            compute_recommendation_accuracy_activity,
            args=[
                tenant_id,
                "2026-01-01",
                "2026-12-31",
            ],
            start_to_close_timeout=timedelta(seconds=120),
        )

        patterns = await workflow.execute_activity(
            detect_recommendation_patterns_activity,
            args=[tenant_id],
            start_to_close_timeout=timedelta(seconds=60),
        )

        adjustments = await workflow.execute_activity(
            suggest_scoring_adjustments_activity,
            args=[tenant_id],
            start_to_close_timeout=timedelta(seconds=60),
        )

        return {
            "accuracy": accuracy,
            "patterns": patterns,
            "adjustments": adjustments,
        }


# ============================================================
# WORKFLOW 4: Feature Materialization Workflow
# ============================================================

@workflow.defn
class FeatureMaterializationWorkflow:
    """
    Continuously materializes features for active feature groups.
    Schedule: Every 15 minutes for REAL_TIME features
    """

    @workflow.run
    async def run(self, tenant_id: str, feature_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        results = []
        if feature_ids:
            for fid in feature_ids:
                result = await workflow.execute_activity(
                    materialize_feature_activity,
                    args=[fid, {}],
                    start_to_close_timeout=timedelta(seconds=60),
                )
                results.append(result)

        return {
            "tenant_id": tenant_id,
            "materialized_count": len(results),
            "results": results,
        }


# ============================================================
# WORKFLOW 5: Model Evaluation Workflow
# ============================================================

@workflow.defn
class ModelEvaluationWorkflow:
    """
    Runs offline evaluation on registered models.
    Triggered: When new model version is submitted for review
    """

    @workflow.run
    async def run(self, model_id: str, version: str) -> Dict[str, Any]:
        eval_result = await workflow.execute_activity(
            evaluate_model_activity,
            args=[model_id, version],
            start_to_close_timeout=timedelta(seconds=300),
        )

        return {
            "model_id": model_id,
            "version": version,
            "evaluation": eval_result,
        }


# ============================================================
# WORKFLOW 6: Executive Memory Sync Workflow
# ============================================================

@workflow.defn
class ExecutiveMemorySyncWorkflow:
    """
    Syncs executive behavior signals to vector memory.
    Runs: Every hour
    """

    @workflow.run
    async def run(self, tenant_id: str) -> Dict[str, Any]:
        sync_result = await workflow.execute_activity(
            sync_executive_profiles_activity,
            args=[tenant_id],
            start_to_close_timeout=timedelta(seconds=120),
        )

        return {
            "tenant_id": tenant_id,
            "sync_result": sync_result,
        }
