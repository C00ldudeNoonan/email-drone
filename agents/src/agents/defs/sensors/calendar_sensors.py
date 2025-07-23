from dagster import sensor, SensorEvaluationContext, RunRequest, SkipReason
from ..jobs.agent_jobs import calendar_analysis_job

@sensor(
    job=calendar_analysis_job,
    minimum_interval_seconds=1800  # 30 minutes
)
def meeting_reminder_sensor(context: SensorEvaluationContext):
    """Trigger calendar analysis for upcoming meetings"""
    
    # This would check for upcoming meetings needing prep
    # For now, return a skip
    return SkipReason("No upcoming meetings requiring prep")