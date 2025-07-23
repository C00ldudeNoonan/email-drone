from dagster import schedule, DefaultScheduleStatus
from ..jobs.agent_jobs import email_processing_job, calendar_analysis_job
from ..jobs.coordination_jobs import daily_intelligence_briefing_job

@schedule(
    job=email_processing_job,
    cron_schedule="0 9,13,17 * * 1-5",  # 9 AM, 1 PM, 5 PM on weekdays
    default_status=DefaultScheduleStatus.RUNNING
)
def morning_briefing_schedule():
    """Morning email processing"""
    return {}

@schedule(
    job=daily_intelligence_briefing_job,
    cron_schedule="0 8 * * 1-5",  # 8 AM weekdays
    default_status=DefaultScheduleStatus.RUNNING
)
def evening_summary_schedule():
    """Evening summary generation"""
    return {}