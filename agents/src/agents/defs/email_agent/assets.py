from dagster import asset, AssetExecutionContext, MetadataValue, Config
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime, timedelta
from .lib.workflows import EmailWorkflow
from ...lib.shared_utils import hash_config, safe_timestamp, extract_domain, AgentLogger

class EmailIngestionConfig(Config):
    """Flexible configuration for email ingestion agent behavior"""
    
    # Basic ingestion controls
    max_emails: int = 50
    email_query: str = "is:unread"
    include_spam: bool = False
    days_back: Optional[int] = None
    
    # Agent behavior controls
    priority_senders: List[str] = []
    skip_categories: List[str] = ["newsletters", "notifications"]
    urgent_keywords: List[str] = ["urgent", "asap", "emergency", "deadline"]
    
    # Filtering intelligence
    min_body_length: int = 10
    exclude_automated: bool = True
    focus_on_work_hours: bool = False
    
    # Agent learning
    learn_from_user_actions: bool = True
    confidence_threshold: float = 0.7

class EmailProcessingConfig(Config):
    """Flexible configuration for email processing agent behavior"""
    
    # Agent decision-making controls
    enable_response_generation: bool = True
    confidence_threshold: float = 0.6
    batch_size: int = 10
    use_direct_gemini: bool = True
    
    # Agent personality and style
    decision_style: str = "conservative"
    response_tone: str = "professional"
    auto_archive_confidence: float = 0.8
    
    # Agent training and personalization
    training_mode: bool = False
    use_training_examples: bool = True
    few_shot_examples_count: int = 5
    learn_from_user_feedback: bool = True
    
    # User-specific training examples
    categorization_examples: List[Dict[str, str]] = []
    response_examples: List[Dict[str, str]] = []
    
    # User preferences for categorization
    custom_category_rules: Dict[str, List[str]] = {}
    vip_senders: List[str] = []
    auto_archive_senders: List[str] = []
    never_archive_domains: List[str] = []
    
    # Agent action controls
    auto_execute_actions: bool = False
    max_actions_per_run: int = 20
    require_human_approval: List[str] = ["delete", "forward"]
    
    # Agent learning and adaptation
    use_conversation_history: bool = True
    max_context_emails: int = 10
    learn_from_corrections: bool = True
    
    # Agent coordination with other agents
    share_insights_with_calendar: bool = True
    share_insights_with_notion: bool = True
    coordinate_meeting_scheduling: bool = True
    
    # Agent constraints and safety
    dry_run_mode: bool = False
    rate_limit_actions: bool = True
    backup_decisions: bool = True

@asset(
    group_name="email_ingestion",
    description="Smart email fetching with agent-driven filtering"
)
def inbox_emails(
    context: AssetExecutionContext,
    gmail_client,
    config: EmailIngestionConfig
) -> List[Dict]:
    """Intelligent email fetching that adapts based on configuration"""
    
    # Build dynamic query
    query_parts = [config.email_query]
    if not config.include_spam:
        query_parts.append("-in:spam")
    if config.days_back:
        query_parts.append(f"newer_than:{config.days_back}d")
    
    dynamic_query = " ".join(query_parts)
    
    # Fetch emails with agent intelligence
    emails = gmail_client.fetch_emails(query=dynamic_query, max_results=config.max_emails)
    
    # Agent-driven filtering
    filtered_emails = []
    priority_count = 0
    urgent_count = 0
    
    for email in emails:
        # Skip if configured to exclude
        if config.exclude_automated and _is_automated_email(email):
            continue
            
        if config.min_body_length and len(email.get('body', '')) < config.min_body_length:
            continue
        
        # Priority sender detection
        if _is_priority_sender(email, config.priority_senders):
            email['is_priority_sender'] = True
            priority_count += 1
        else:
            email['is_priority_sender'] = False
        
        # Urgent keyword detection
        if _contains_urgent_keywords(email, config.urgent_keywords):
            email['has_urgent_keywords'] = True
            email['agent_priority_boost'] = True
            urgent_count += 1
        else:
            email['has_urgent_keywords'] = False
            email['agent_priority_boost'] = False
        
        # Agent metadata
        email['agent_processed_at'] = safe_timestamp()
        email['agent_confidence'] = _calculate_email_confidence(email, config)
        
        filtered_emails.append(email)
    
    context.add_output_metadata({
        "total_fetched": len(emails),
        "total_filtered": len(filtered_emails),
        "priority_senders": priority_count,
        "urgent_emails": urgent_count,
        "query_used": dynamic_query,
        "agent_config_hash": hash_config(config.__dict__),
        "avg_confidence": sum(e['agent_confidence'] for e in filtered_emails) / len(filtered_emails) if filtered_emails else 0
    })
    
    AgentLogger.log_decision(context, "EmailIngestion", {"filtered": len(filtered_emails), "from": len(emails)}, 
                           sum(e['agent_confidence'] for e in filtered_emails) / len(filtered_emails) if filtered_emails else 0)
    
    return filtered_emails

@asset(
    group_name="email_ingestion",
    description="Structured email data ready for processing"
)
def structured_emails(
    context: AssetExecutionContext,
    inbox_emails: List[Dict]
) -> pd.DataFrame:
    """Convert raw emails to structured DataFrame"""
    
    if not inbox_emails:
        return pd.DataFrame()
    
    df = pd.DataFrame(inbox_emails)
    
    # Data cleaning and enrichment
    df['subject'] = df['subject'].fillna('(No Subject)')
    df['from_email'] = df['from_email'].fillna('Unknown Sender')
    df['body_length'] = df['body'].fillna('').str.len()
    df['has_attachments'] = df['labels'].apply(
        lambda labels: 'ATTACHMENT' in labels if isinstance(labels, list) else False
    )
    df['fetch_timestamp'] = pd.Timestamp.now()
    df['sender_domain'] = df['from_email'].apply(extract_domain)
    
    context.add_output_metadata({
        "total_emails": len(df),
        "unique_senders": df['from_email'].nunique(),
        "unique_domains": df['sender_domain'].nunique(),
        "avg_body_length": round(df['body_length'].mean(), 2),
        "emails_with_attachments": df['has_attachments'].sum()
    })
    
    return df

@asset(
    group_name="email_training",
    description="Collect user feedback and training data for email agent"
)
def email_training_data(
    context: AssetExecutionContext,
    gmail_client,
    config: EmailProcessingConfig
) -> pd.DataFrame:
    """Collect training data from user's historical email actions"""
    
    if not config.learn_from_user_feedback:
        return pd.DataFrame()
    
    training_examples = []
    
    # Add explicit examples from config
    for example in config.categorization_examples:
        training_examples.append({
            'email_id': f"config_example_{len(training_examples)}",
            'email_snippet': example['email_snippet'],
            'subject': example.get('subject', ''),
            'from_domain': '',
            'user_action': 'explicit_training',
            'inferred_category': example['correct_category'],
            'inferred_priority': _priority_from_category(example['correct_category']),
            'confidence': 1.0,
            'source': 'user_config',
            'reasoning': example.get('reasoning', ''),
            'timestamp': pd.Timestamp.now()
        })
    
    training_df = pd.DataFrame(training_examples)
    
    context.add_output_metadata({
        "total_training_examples": len(training_df),
        "explicit_examples": len(config.categorization_examples)
    })
    
    return training_df

@asset(
    group_name="email_training", 
    description="User feedback collection for improving email agent decisions"
)
def user_feedback_data(
    context: AssetExecutionContext,
    config: EmailProcessingConfig
) -> pd.DataFrame:
    """Collect and store user feedback on agent decisions"""
    
    # Placeholder for feedback data - in production this would come from UI
    feedback_examples = []
    feedback_df = pd.DataFrame(feedback_examples)
    
    context.add_output_metadata({
        "total_feedback_entries": len(feedback_df)
    })
    
    return feedback_df

@asset(
    group_name="email_training",
    description="Generate personalized prompts using training data"
)
def personalized_email_prompts(
    context: AssetExecutionContext,
    email_training_data: pd.DataFrame,
    user_feedback_data: pd.DataFrame,
    config: EmailProcessingConfig
) -> Dict[str, str]:
    """Generate personalized prompts that include user-specific examples"""
    
    prompts = {}
    
    if email_training_data.empty and not config.categorization_examples:
        return {}
    
    # Build personalized categorization prompt
    if not email_training_data.empty or config.categorization_examples:
        examples_text = ""
        if not email_training_data.empty:
            for _, example in email_training_data.head(config.few_shot_examples_count).iterrows():
                examples_text += f"Example: {example['email_snippet']} → {example['inferred_category']}\n"
        
        prompts['personalized_categorization'] = f"""
Based on these user-specific examples:
{examples_text}

User Rules:
- VIP Senders: {', '.join(config.vip_senders)}
- Auto-archive: {', '.join(config.auto_archive_senders)}
- Custom rules: {config.custom_category_rules}

Categorize the email following these patterns.
"""
    
    context.add_output_metadata({
        "prompts_generated": len(prompts),
        "training_examples_used": len(email_training_data) if not email_training_data.empty else 0
    })
    
    return prompts

@asset(
    group_name="email_processing",
    description="AI agent for intelligent email processing with personalized training"
)
def processed_emails(
    context: AssetExecutionContext,
    structured_emails: pd.DataFrame,
    llm_client,
    personalized_email_prompts: Dict[str, str],
    email_training_data: pd.DataFrame,
    config: EmailProcessingConfig
) -> pd.DataFrame:
    """Email processing agent that uses personalized training and user patterns"""
    
    if structured_emails.empty:
        return pd.DataFrame()
    
    # Initialize agent
    agent_context = _initialize_agent_context(config, context)
    
    # Get LLM client and create workflow
    client = llm_client.setup_for_execution(context)
    workflow = EmailWorkflow(
        client, 
        agent_config=config,
        personalized_prompts=personalized_email_prompts,
        training_data=email_training_data
    )
    
    results = []
    processed_count = 0
    training_applied_count = 0
    
    # Process emails with agent intelligence
    for batch_start in range(0, len(structured_emails), config.batch_size):
        batch_end = min(batch_start + config.batch_size, len(structured_emails))
        batch = structured_emails.iloc[batch_start:batch_end]
        
        for idx, email_row in batch.iterrows():
            try:
                email_dict = email_row.to_dict()
                
                # Find similar training examples
                similar_training = _find_similar_training_examples(email_dict, email_training_data, config)
                
                # Process with training
                agent_decision = workflow.process_email_with_training(
                    email_dict, [], agent_context, similar_training
                )
                
                # Apply user-specific rules
                enhanced_decision = _apply_user_rules(agent_decision, email_dict, config, context)
                
                if enhanced_decision.get('training_applied', False):
                    training_applied_count += 1
                
                # Build result
                processed_email = {
                    'email_id': email_dict['id'],
                    'subject': email_dict.get('subject', ''),
                    'from_email': email_dict.get('from_email', ''),
                    'sender_domain': email_dict.get('sender_domain', ''),
                    'category': enhanced_decision['category'],
                    'confidence': enhanced_decision['confidence'],
                    'priority': enhanced_decision['priority'],
                    'sentiment': enhanced_decision['sentiment'],
                    'action_items': enhanced_decision['action_items'],
                    'action_count': len(enhanced_decision['action_items']),
                    'should_archive': enhanced_decision['should_archive'],
                    'meeting_needed': enhanced_decision['meeting_needed'],
                    'training_applied': enhanced_decision.get('training_applied', False),
                    'processing_timestamp': pd.Timestamp.now()
                }
                
                results.append(processed_email)
                processed_count += 1
                
            except Exception as e:
                context.log.error(f"Failed to process email {email_dict.get('id', 'unknown')}: {e}")
                continue
    
    df = pd.DataFrame(results)
    
    if not df.empty:
        context.add_output_metadata({
            "total_processed": len(df),
            "training_applied_count": training_applied_count,
            "training_application_rate": round(training_applied_count / len(df) * 100, 2),
            "category_breakdown": MetadataValue.json(df['category'].value_counts().to_dict()),
            "avg_confidence": round(df['confidence'].mean(), 3)
        })
        
        AgentLogger.log_training_applied(context, "EmailProcessing", training_applied_count, 
                                       training_applied_count / len(df) if len(df) > 0 else 0)
    
    return df

# Helper functions
def _is_automated_email(email: Dict) -> bool:
    """Detect if email is automated"""
    automated_indicators = ['noreply', 'no-reply', 'donotreply', 'automated']
    from_email = email.get('from_email', '').lower()
    return any(indicator in from_email for indicator in automated_indicators)

def _is_priority_sender(email: Dict, priority_senders: List[str]) -> bool:
    """Check if email is from a priority sender"""
    from_email = email.get('from_email', '').lower()
    sender_domain = email.get('sender_domain', '').lower()
    return any(priority.lower() in from_email or priority.lower() in sender_domain 
              for priority in priority_senders)

def _contains_urgent_keywords(email: Dict, urgent_keywords: List[str]) -> bool:
    """Check if email contains urgent keywords"""
    content = f"{email.get('subject', '')} {email.get('body', '')}".lower()
    return any(keyword.lower() in content for keyword in urgent_keywords)

def _calculate_email_confidence(email: Dict, config: EmailIngestionConfig) -> float:
    """Calculate agent confidence in email importance"""
    confidence = 0.5
    if email.get('is_priority_sender'):
        confidence += 0.3
    if email.get('has_urgent_keywords'):
        confidence += 0.2
    return min(1.0, confidence)

def _priority_from_category(category: str) -> int:
    """Map category to priority level"""
    priority_map = {
        'marketing': 1, 'notification': 2, 'personal': 3,
        'work': 4, 'meeting_request': 4, 'action_required': 5
    }
    return priority_map.get(category, 3)

def _find_similar_training_examples(email: Dict, training_data: pd.DataFrame, config: EmailProcessingConfig) -> List[Dict]:
    """Find training examples similar to current email"""
    if training_data.empty:
        return []
    
    similar_examples = []
    email_domain = email.get('sender_domain', '').lower()
    
    # Look for examples with same domain
    domain_matches = training_data[training_data['from_domain'].str.lower() == email_domain]
    similar_examples.extend(domain_matches.to_dict('records'))
    
    return similar_examples[:3]  # Limit to top 3

def _apply_user_rules(decision: Dict, email: Dict, config: EmailProcessingConfig, context: AssetExecutionContext) -> Dict:
    """Apply user-specific rules learned from training"""
    enhanced_decision = decision.copy()
    user_rules_applied = []
    training_applied = False
    
    from_email = email.get('from_email', '').lower()
    sender_domain = email.get('sender_domain', '').lower()
    
    # Apply VIP sender rules
    if any(vip.lower() in from_email or vip.lower() in sender_domain for vip in config.vip_senders):
        enhanced_decision['priority'] = max(enhanced_decision['priority'], 4)
        enhanced_decision['should_archive'] = False
        user_rules_applied.append('vip_sender_priority_boost')
        training_applied = True
    
    # Apply auto-archive sender rules
    if any(arch.lower() in from_email or arch.lower() in sender_domain for arch in config.auto_archive_senders):
        enhanced_decision['should_archive'] = True
        enhanced_decision['category'] = 'marketing'
        user_rules_applied.append('auto_archive_sender')
        training_applied = True
    
    enhanced_decision['training_applied'] = training_applied
    enhanced_decision['user_rules_applied'] = user_rules_applied
    
    return enhanced_decision

def _initialize_agent_context(config: EmailProcessingConfig, context: AssetExecutionContext) -> Dict:
    """Initialize agent context"""
    import uuid
    return {
        "session_id": str(uuid.uuid4())[:8],
        "start_time": safe_timestamp(),
        "decision_style": config.decision_style
    }


