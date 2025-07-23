"""Shared utilities across all agents."""

import hashlib
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

def hash_config(config_dict: Dict[str, Any]) -> str:
    """Create hash of configuration for change detection."""
    config_str = str(sorted(config_dict.items()))
    return hashlib.md5(config_str.encode()).hexdigest()[:8]

def safe_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return pd.Timestamp.now().isoformat()

def extract_domain(email: str) -> str:
    """Extract domain from email address."""
    try:
        return email.split('@')[1].lower()
    except (IndexError, AttributeError):
        return ""

def calculate_confidence_boost(factors: List[str]) -> float:
    """Calculate confidence boost based on factors."""
    boost_map = {
        'vip_sender': 0.3,
        'urgent_keywords': 0.2,
        'user_pattern': 0.25,
        'domain_trust': 0.15,
        'content_quality': 0.1
    }
    
    total_boost = sum(boost_map.get(factor, 0) for factor in factors)
    return min(0.5, total_boost)  # Cap at 0.5

def format_agent_metadata(agent_name: str, session_id: str, **kwargs) -> Dict[str, Any]:
    """Format standard agent metadata."""
    return {
        'agent_name': agent_name,
        'session_id': session_id,
        'timestamp': safe_timestamp(),
        'version': '1.0',
        **kwargs
    }

class AgentLogger:
    """Shared logging utilities for agents."""
    
    @staticmethod
    def log_decision(context, agent_name: str, decision: Dict[str, Any], confidence: float):
        """Log agent decision with standardized format."""
        context.log.info(
            f"{agent_name} decision: {decision.get('action', 'unknown')} "
            f"(confidence: {confidence:.3f})"
        )
    
    @staticmethod
    def log_training_applied(context, agent_name: str, examples_used: int, boost: float):
        """Log when training data is applied."""
        context.log.info(
            f"{agent_name} applied training: {examples_used} examples, "
            f"confidence boost: +{boost:.3f}"
        )
    
    @staticmethod
    def log_coordination(context, source_agent: str, target_agent: str, insights: Dict):
        """Log cross-agent coordination."""
        context.log.info(
            f"Coordination: {source_agent} → {target_agent}, "
            f"insights: {list(insights.keys())}"
        )