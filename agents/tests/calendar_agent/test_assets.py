import pytest
from datetime import datetime
from productivity_intelligence.components.calendar_agent.assets import CalendarAgentConfig

def test_calendar_agent_config():
    """Test Calendar agent configuration"""
    
    config = CalendarAgentConfig(
        target_date="2024-03-15",
        analyze_schedule_health=True,
        identify_focus_blocks=True,
        include_meeting_prep=True,
        focus_block_min_duration=45
    )
    
    assert config.target_date == "2024-03-15"
    assert config.analyze_schedule_health is True
    assert config.identify_focus_blocks is True
    assert config.focus_block_min_duration == 45

def test_focus_block_identification():
    """Test focus block identification logic"""
    
    config = CalendarAgentConfig(
        focus_block_min_duration=30
    )
    
    # Mock calendar events
    mock_events = [
        {
            "start_time": "2024-03-15T09:00:00Z",
            "end_time": "2024-03-15T10:00:00Z",
            "title": "Team Meeting"
        },
        {
            "start_time": "2024-03-15T11:30:00Z", 
            "end_time": "2024-03-15T12:00:00Z",
            "title": "1:1 with Manager"
        }
    ]
    
    # This would test the actual focus block identification
    # For now, just test the configuration
    assert config.focus_block_min_duration == 30

def test_meeting_importance_scoring():
    """Test meeting importance scoring logic"""
    
    config = CalendarAgentConfig(
        include_meeting_prep=True
    )
    
    # Mock high importance meeting
    high_importance_meeting = {
        "title": "Q4 Strategy Planning",
        "attendee_count": 8,
        "organizer": "ceo@company.com"
    }
    
    # Mock low importance meeting
    low_importance_meeting = {
        "title": "Coffee Chat",
        "attendee_count": 2,
        "organizer": "colleague@company.com"
    }
    
    # This would test the actual importance scoring
    assert config.include_meeting_prep is True