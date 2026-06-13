"""
Temporal worker for the Healthcare Financial Intelligence Platform.
Registers all Phase 3.5 activities and workflows.
"""
import asyncio
import logging
import os

from temporalio.client import Client
from temporalio.worker import Worker

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
from app.infrastructure.temporal.workflows import (
    DecisionTrackingWorkflow,
    OutcomeMeasurementWorkflow,
    LearningWorkflow,
    FeatureMaterializationWorkflow,
    ModelEvaluationWorkflow,
    ExecutiveMemorySyncWorkflow,
)

logger = logging.getLogger(__name__)

TASK_QUEUE = "healthcare-fi-platform"
TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "temporal:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")

ACTIVITIES = [
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
]

WORKFLOWS = [
    DecisionTrackingWorkflow,
    OutcomeMeasurementWorkflow,
    LearningWorkflow,
    FeatureMaterializationWorkflow,
    ModelEvaluationWorkflow,
    ExecutiveMemorySyncWorkflow,
]


async def main():
    """Start the Temporal worker with retry logic."""
    logger.info(f"Connecting to Temporal at {TEMPORAL_HOST}, namespace={TEMPORAL_NAMESPACE}")

    client = None
    for attempt in range(30):
        try:
            client = await Client.connect(TEMPORAL_HOST, namespace=TEMPORAL_NAMESPACE)
            logger.info("Temporal worker connected successfully.")
            break
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/30: Temporal not ready: {e}")
            await asyncio.sleep(5)

    if client is None:
        logger.error("Failed to connect to Temporal after 30 attempts. Exiting.")
        return

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=WORKFLOWS,
        activities=ACTIVITIES,
    )

    logger.info(f"Temporal worker starting on task queue: {TASK_QUEUE}")
    logger.info(f"Registered {len(ACTIVITIES)} activities, {len(WORKFLOWS)} workflows")

    await worker.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
