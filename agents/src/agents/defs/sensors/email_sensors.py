from dagster import sensor, SensorEvaluationContext, RunRequest, SkipReason
from ..jobs.agent_jobs import email_processing_job
import time

@sensor(
    job=email_processing_job,
    minimum_interval_seconds=300
)
def urgent_email_sensor(context: SensorEvaluationContext):
    """Trigger processing for urgent emails"""
    
    # This would check for urgent emails in practice
    # For now, return a skip
    return SkipReason("No urgent emails detected")