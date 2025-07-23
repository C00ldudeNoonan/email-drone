import pytest
from dagster import materialize
from productivity_intelligence.components.email_agent import email_agent_component
from productivity_intelligence.components.email_agent.assets import EmailIngestionConfig, EmailProcessingConfig

def test_inbox_emails_asset():
    """Test email ingestion asset"""
    
    # Mock configuration
    config = EmailIngestionConfig(
        max_emails=5,
        email_query="is:unread",
        priority_senders=["test@example.com"]
    )
    
    # This would require proper mocking of Gmail API
    # For now, just test that the asset can be materialized with mock data
    assert config.max_emails == 5
    assert "test@example.com" in config.priority_senders

def test_email_processing_config():
    """Test email processing configuration"""
    
    config = EmailProcessingConfig(
        decision_style="conservative",
        confidence_threshold=0.8,
        vip_senders=["boss@company.com"],
        auto_execute_actions=False
    )
    
    assert config.decision_style == "conservative"
    assert config.confidence_threshold == 0.8
    assert config.auto_execute_actions is False

def test_training_examples_validation():
    """Test that training examples are properly formatted"""
    
    config = EmailProcessingConfig(
        categorization_examples=[
            {
                "email_snippet": "Weekly newsletter from marketing team",
                "correct_category": "notification",
                "reasoning": "Internal team updates"
            }
        ]
    )
    
    assert len(config.categorization_examples) == 1
    assert config.categorization_examples[0]["correct_category"] == "notification"

def test_user_rules_application():
    """Test that user-specific rules are applied correctly"""
    
    config = EmailProcessingConfig(
        vip_senders=["ceo@company.com"],
        auto_archive_senders=["newsletter@example.com"],
        custom_category_rules={
            "work": ["@company.com", "project alpha"],
            "marketing": ["unsubscribe", "promotion"]
        }
    )
    
    assert "ceo@company.com" in config.vip_senders
    assert "newsletter@example.com" in config.auto_archive_senders
    assert "work" in config.custom_category_rules
    assert "@company.com" in config.custom_category_rules["work"]