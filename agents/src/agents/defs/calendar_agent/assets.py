from dagster import asset, AssetExecutionContext, MetadataValue, Config
from .lib.workflows import CalendarWorkflow
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List

class CalendarAgentConfig(Config):
    """Flexible configuration for calendar intelligence agent"""
    target_date: str = ""
    analyze_schedule_health: bool = True
    identify_focus_blocks: bool = True
    include_meeting_prep: bool = True
    analysis_depth: str = "standard"
    focus_block_min_duration: int = 30

@asset(
    group_name="calendar_intelligence",
    description="Daily calendar events and schedule"
)
def daily_calendar_events(
    context: AssetExecutionContext,
    calendar_client,
    config: CalendarAgentConfig
) -> List[Dict]:
    """Fetch daily calendar events"""
    
    if config.target_date:
        target_date = datetime.fromisoformat(config.target_date)
    else:
        target_date = datetime.now()
    
    calendar_service = calendar_client.setup_for_execution(context)
    events = calendar_service.get_daily_events(target_date)
    
    # Enhance events with agent analysis
    enhanced_events = []
    for event in events:
        enhanced_event = event.copy()
        
        # Agent importance scoring
        importance_score = 0.5
        title = event.get('title', '').lower()
        if any(keyword in title for keyword in ['strategy', 'planning', 'review']):
            importance_score += 0.3
        if event.get('attendee_count', 0) > 5:
            importance_score += 0.2
        
        enhanced_event['agent_importance_score'] = min(1.0, importance_score)
        enhanced_events.append(enhanced_event)
    
    context.add_output_metadata({
        "total_events": len(events),
        "target_date": target_date.date().isoformat(),
        "event_types": MetadataValue.json({
            event_type: len([e for e in events if e.get("event_type") == event_type])
            for event_type in set(e.get("event_type", "meeting") for e in events)
        })
    })
    
    return enhanced_events

@asset(
    group_name="calendar_intelligence",
    description="AI-generated daily schedule summary and insights"
)
def daily_schedule_summary(
    context: AssetExecutionContext,
    daily_calendar_events: List[Dict],
    llm_client,
    config: CalendarAgentConfig
) -> Dict:
    """Generate intelligent daily schedule summary"""
    
    llm = llm_client.setup_for_execution(context)
    workflow = CalendarWorkflow(llm)
    
    # Generate analysis
    analysis = workflow.analyze_daily_schedule(daily_calendar_events, config)
    
    context.add_output_metadata({
        "schedule_health": analysis.get("schedule_health", "unknown"),
        "total_meetings": analysis.get("total_meetings", 0),
        "focus_time_blocks": len(analysis.get("focus_time_opportunities", [])),
        "meeting_prep_items": len(analysis.get("meeting_prep", []))
    })
    
    return analysis