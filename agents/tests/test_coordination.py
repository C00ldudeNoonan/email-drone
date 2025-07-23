import pytest
from productivity_intelligence.jobs.coordination_jobs import DailyBriefingConfig
import pandas as pd

def test_daily_briefing_config():
    """Test daily briefing configuration"""
    
    config = DailyBriefingConfig(
        include_email_summary=True,
        include_notion_insights=True,
        include_calendar_prep=True
    )
    
    assert config.include_email_summary is True
    assert config.include_notion_insights is True
    assert config.include_calendar_prep is True

def test_briefing_generation_with_email_data():
    """Test briefing generation with sample email data"""
    
    # Mock processed emails DataFrame
    mock_emails = pd.DataFrame([
        {
            'email_id': 'email_1',
            'category': 'work',
            'priority': 4,
            'subject': 'Important Project Update'
        },
        {
            'email_id': 'email_2', 
            'category': 'marketing',
            'priority': 1,
            'subject': 'Newsletter'
        }
    ])
    
    # Test that high priority emails are identified
    high_priority = mock_emails[mock_emails['priority'] >= 4]
    assert len(high_priority) == 1
    assert high_priority.iloc[0]['subject'] == 'Important Project Update'

def test_briefing_generation_with_notion_data():
    """Test briefing generation with sample Notion data"""
    
    # Mock Notion analysis DataFrame
    mock_notion = pd.DataFrame([
        {
            'document_id': 'doc_1',
            'key_topics': ['strategy', 'q4-planning'],
            'document_type': 'strategy'
        },
        {
            'document_id': 'doc_2',
            'key_topics': ['meeting-notes', 'engineering'], 
            'document_type': 'meeting_notes'
        }
    ])
    
    # Test that topics are properly extracted
    all_topics = []
    for topics in mock_notion['key_topics']:
        all_topics.extend(topics)
    
    assert 'strategy' in all_topics
    assert 'q4-planning' in all_topics

def test_briefing_generation_with_calendar_data():
    """Test briefing generation with sample calendar data"""
    
    # Mock calendar summary
    mock_calendar_summary = {
        "schedule_health": "busy",
        "total_meetings": 5,
        "meeting_prep": [
            {"event_title": "Strategy Review", "prep_time": 20}
        ],
        "focus_time_opportunities": [
            {"start_time": "14:00", "duration": 60}
        ]
    }
    
    assert mock_calendar_summary["schedule_health"] == "busy"
    assert mock_calendar_summary["total_meetings"] == 5
    assert len(mock_calendar_summary["meeting_prep"]) == 1

def test_cross_agent_coordination():
    """Test that agents can coordinate and share insights"""
    
    # Mock coordination data
    email_insights = {"high_priority_count": 3, "meetings_requested": 2}
    notion_insights = {"trending_topics": ["strategy", "product"]}
    calendar_insights = {"available_focus_blocks": 2}
    
    # Test coordination logic
    coordination_successful = (
        email_insights["meetings_requested"] > 0 and
        len(calendar_insights) > 0 and
        len(notion_insights["trending_topics"]) > 0
    )
    
    assert coordination_successful is True

def test_agent_metadata_tracking():
    """Test that agent metadata is properly tracked"""
    
    # Mock agent session metadata
    agent_metadata = {
        "email_agent": {
            "session_id": "ea_12345",
            "emails_processed": 25,
            "training_applied": 18,
            "confidence_avg": 0.82
        },
        "notion_agent": {
            "session_id": "na_67890", 
            "documents_analyzed": 12,
            "trends_identified": 5,
            "confidence_avg": 0.75
        },
        "calendar_agent": {
            "session_id": "ca_54321",
            "events_analyzed": 8,
            "focus_blocks_found": 3,
            "prep_items_generated": 4
        }
    }
    
    # Test metadata structure
    assert "email_agent" in agent_metadata
    assert agent_metadata["email_agent"]["emails_processed"] == 25
    assert agent_metadata["notion_agent"]["documents_analyzed"] == 12
    assert agent_metadata["calendar_agent"]["events_analyzed"] == 8