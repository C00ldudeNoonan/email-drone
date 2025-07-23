from dagster import schedule, DefaultScheduleStatus
from ..jobs.agent_jobs import notion_intelligence_job

@schedule(
    job=notion_intelligence_job,
    cron_schedule="0 9 * * 1",  # Monday mornings
    default_status=DefaultScheduleStatus.RUNNING
)
def weekly_trend_report_schedule():
    """Weekly Notion trend analysis"""
    return {}