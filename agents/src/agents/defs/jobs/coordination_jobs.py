from dagster import job, op, Config, OpExecutionContext
from datetime import datetime
import pandas as pd

class DailyBriefingConfig(Config):
    """Configuration for daily intelligence briefing"""
    include_email_summary: bool = True
    include_notion_insights: bool = True
    include_calendar_prep: bool = True

@op
def generate_daily_briefing(
    context: OpExecutionContext,
    processed_emails: pd.DataFrame,
    notion_document_analysis: pd.DataFrame,
    daily_schedule_summary: dict,
    config: DailyBriefingConfig
) -> dict:
    """Generate comprehensive daily intelligence briefing"""
    
    briefing = {
        "date": datetime.now().date().isoformat(),
        "sections": {},
        "generated_at": datetime.now().isoformat()
    }
    
    # Email summary
    if config.include_email_summary and not processed_emails.empty:
        high_priority_emails = processed_emails[processed_emails['priority'] >= 4]
        briefing["sections"]["email"] = {
            "total_processed": len(processed_emails),
            "high_priority": len(high_priority_emails),
            "categories": processed_emails['category'].value_counts().head(3).to_dict()
        }
    
    # Notion insights
    if config.include_notion_insights and not notion_document_analysis.empty:
        briefing["sections"]["notion"] = {
            "documents_analyzed": len(notion_document_analysis),
            "top_topics": notion_document_analysis['key_topics'].explode().value_counts().head(3).to_dict()
        }
    
    # Calendar preparation
    if config.include_calendar_prep and daily_schedule_summary:
        briefing["sections"]["calendar"] = {
            "schedule_health": daily_schedule_summary.get("schedule_health"),
            "total_meetings": daily_schedule_summary.get("total_meetings", 0),
            "prep_required": len(daily_schedule_summary.get("meeting_prep", []))
        }
    
    context.log.info(f"Generated daily briefing with {len(briefing['sections'])} sections")
    return briefing

@job
def daily_intelligence_briefing_job():
    """Daily job that coordinates all agents for intelligence briefing"""
    generate_daily_briefing()