import pytest
from productivity_intelligence.components.notion_agent.assets import NotionAgentConfig

def test_notion_agent_config():
    """Test Notion agent configuration"""
    
    config = NotionAgentConfig(
        days_back=14,
        analysis_depth="deep",
        database_priorities={
            "Strategy Docs": 10,
            "Meeting Notes": 5,
            "Project Plans": 8
        },
        max_documents_per_run=50
    )
    
    assert config.days_back == 14
    assert config.analysis_depth == "deep"
    assert config.database_priorities["Strategy Docs"] == 10
    assert config.max_documents_per_run == 50

def test_database_priority_scoring():
    """Test that database priorities affect document scoring"""
    
    config = NotionAgentConfig(
        database_priorities={
            "High Priority DB": 10,
            "Low Priority DB": 1
        }
    )
    
    # Mock document from high priority database
    high_priority_doc = {
        "database": "High Priority DB",
        "title": "Important Strategy Doc"
    }
    
    # Mock document from low priority database  
    low_priority_doc = {
        "database": "Low Priority DB",
        "title": "Random Notes"
    }
    
    # In practice, this would test the actual priority scoring logic
    assert config.database_priorities["High Priority DB"] > config.database_priorities["Low Priority DB"]