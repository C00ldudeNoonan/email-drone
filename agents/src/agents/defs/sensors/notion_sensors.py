from dagster import sensor, SensorEvaluationContext, RunRequest, SkipReason
from ..jobs.agent_jobs import notion_intelligence_job

@sensor(
    job=notion_intelligence_job,
    minimum_interval_seconds=3600
)
def new_document_sensor(context: SensorEvaluationContext):
    """Trigger analysis when new documents are detected"""
    
    # This would check for new Notion documents in practice
    # For now, return a skip
    return SkipReason("No new documents detected")