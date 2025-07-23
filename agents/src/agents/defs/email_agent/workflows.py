from langgraph.graph import StateGraph, END
from langchain.prompts import ChatPromptTemplate
from typing import TypedDict, List, Dict, Any, Optional
from .prompts import (
    EMAIL_CATEGORIZATION_PROMPT,
    PRIORITY_ASSESSMENT_PROMPT, 
    ACTION_EXTRACTION_PROMPT,
    MEETING_DETECTION_PROMPT,
    PERSONALIZED_CATEGORIZATION_PROMPT
)
import json
import pandas as pd

class EmailProcessingState(TypedDict):
    """State for email processing workflow"""
    email: Dict[str, Any]
    category: str
    confidence: float
    priority: int
    urgency_indicators: List[str]
    action_items: List[Dict[str, str]]
    should_archive: bool
    meeting_needed: bool
    meeting_context: Dict[str, Any]
    tags: List[str]
    sentiment: str
    suggested_response: Optional[str]
    processing_metadata: Dict[str, Any]

class EmailWorkflow:
    """LangGraph-based email processing workflow with personalization"""
    
    def __init__(self, llm_client, agent_config=None, personalized_prompts=None, training_data=None):
        self.llm = llm_client
        self.agent_config = agent_config or {}
        self.personalized_prompts = personalized_prompts or {}
        self.training_data = training_data
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the email processing state graph"""
        workflow = StateGraph(EmailProcessingState)
        
        # Add processing nodes
        workflow.add_node("categorize", self._categorize_email)
        workflow.add_node("assess_priority", self._assess_priority)
        workflow.add_node("detect_urgency", self._detect_urgency_indicators)
        workflow.add_node("extract_actions", self._extract_action_items)
        workflow.add_node("analyze_sentiment", self._analyze_sentiment)
        workflow.add_node("detect_meetings", self._detect_meeting_requests)
        workflow.add_node("generate_tags", self._generate_tags)
        workflow.add_node("suggest_response", self._suggest_response)
        workflow.add_node("finalize", self._finalize_processing)
        
        # Define workflow edges
        workflow.set_entry_point("categorize")
        workflow.add_edge("categorize", "assess_priority")
        workflow.add_edge("assess_priority", "detect_urgency")
        workflow.add_edge("detect_urgency", "extract_actions")
        workflow.add_edge("extract_actions", "analyze_sentiment")
        workflow.add_edge("analyze_sentiment", "detect_meetings")
        workflow.add_edge("detect_meetings", "generate_tags")
        workflow.add_edge("generate_tags", "suggest_response")
        workflow.add_edge("suggest_response", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _categorize_email(self, state: EmailProcessingState) -> EmailProcessingState:
        """Categorize email with personalized training if available"""
        email = state["email"]
        
        # Use personalized prompt if available
        if 'personalized_categorization' in self.personalized_prompts:
            prompt = self.personalized_prompts['personalized_categorization']
            
            # Add training context
            training_examples = ""
            if self.training_data is not None and not self.training_data.empty:
                examples = self.training_data.head(3)
                for _, example in examples.iterrows():
                    training_examples += f"- {example['email_snippet']} → {example['inferred_category']}\n"
            
            response = self.llm.invoke(prompt.format(
                training_examples=training_examples,
                feedback_insights="Recent patterns from user behavior",
                vip_senders=", ".join(getattr(self.agent_config, 'vip_senders', [])),
                auto_archive_senders=", ".join(getattr(self.agent_config, 'auto_archive_senders', [])),
                custom_rules=str(getattr(self.agent_config, 'custom_category_rules', {})),
                subject=email.get("subject", ""),
                from_email=email.get("from_email", ""),
                content=email.get("snippet", "")[:500]
            ))
        else:
            # Use default prompt
            response = self.llm.invoke(EMAIL_CATEGORIZATION_PROMPT.format(
                subject=email.get("subject", ""),
                from_email=email.get("from_email", ""),
                sender_domain=email.get("sender_domain", ""),
                content=email.get("snippet", "")[:500]
            ))
        
        try:
            result = json.loads(response.content)
            state["category"] = result.get("category", "unknown")
            state["confidence"] = min(1.0, max(0.0, result.get("confidence", 0.5)))
        except json.JSONDecodeError:
            state["category"] = "unknown"
            state["confidence"] = 0.0
        
        return state
    
    def _assess_priority(self, state: EmailProcessingState) -> EmailProcessingState:
        """Assess email priority with contextual analysis"""
        email = state["email"]
        
        response = self.llm.invoke(PRIORITY_ASSESSMENT_PROMPT.format(
            category=state["category"],
            subject=email.get("subject", ""),
            from_email=email.get("from_email", ""),
            content=email.get("snippet", ""),
            body_length=len(email.get("body", ""))
        ))
        
        try:
            priority = int(response.content.strip())
            state["priority"] = max(1, min(5, priority))
        except ValueError:
            state["priority"] = 3
        
        return state
    
    def _detect_urgency_indicators(self, state: EmailProcessingState) -> EmailProcessingState:
        """Detect urgency indicators in email content"""
        email = state["email"]
        content = f"{email.get('subject', '')} {email.get('body', '')}"
        
        urgency_keywords = [
            'urgent', 'asap', 'emergency', 'critical', 'immediate',
            'deadline', 'today', 'now', 'quickly', 'rush'
        ]
        
        found_indicators = [
            keyword for keyword in urgency_keywords 
            if keyword.lower() in content.lower()
        ]
        
        state["urgency_indicators"] = found_indicators
        
        # Boost priority if urgency indicators found
        if found_indicators and state["priority"] < 4:
            state["priority"] = min(5, state["priority"] + 1)
        
        return state
    
    def _extract_action_items(self, state: EmailProcessingState) -> EmailProcessingState:
        """Extract structured action items"""
        if state["category"] in ["marketing", "notification", "social"]:
            state["action_items"] = []
            return state
        
        email = state["email"]
        response = self.llm.invoke(ACTION_EXTRACTION_PROMPT.format(
            subject=email.get("subject", ""),
            content=email.get("body", email.get("snippet", ""))
        ))
        
        try:
            actions = json.loads(response.content)
            if isinstance(actions, list):
                state["action_items"] = actions
            else:
                state["action_items"] = []
        except json.JSONDecodeError:
            state["action_items"] = []
        
        return state
    
    def _analyze_sentiment(self, state: EmailProcessingState) -> EmailProcessingState:
        """Analyze email sentiment"""
        email = state["email"]
        content = f"{email.get('subject', '')} {email.get('body', email.get('snippet', ''))}"
        
        # Simple sentiment analysis (could be enhanced with dedicated sentiment model)
        positive_words = ['thank', 'great', 'excellent', 'pleased', 'happy', 'appreciate']
        negative_words = ['problem', 'issue', 'concern', 'urgent', 'disappointed', 'error']
        
        positive_count = sum(1 for word in positive_words if word in content.lower())
        negative_count = sum(1 for word in negative_words if word in content.lower())
        
        if positive_count > negative_count:
            state["sentiment"] = "positive"
        elif negative_count > positive_count:
            state["sentiment"] = "negative"
        else:
            state["sentiment"] = "neutral"
        
        return state
    
    def _detect_meeting_requests(self, state: EmailProcessingState) -> EmailProcessingState:
        """Detect and analyze meeting requests"""
        email = state["email"]
        
        response = self.llm.invoke(MEETING_DETECTION_PROMPT.format(
            subject=email.get("subject", ""),
            content=email.get("body", email.get("snippet", "")),
            from_email=email.get("from_email", "")
        ))
        
        try:
            result = json.loads(response.content)
            state["meeting_needed"] = result.get("needs_meeting", False)
            state["meeting_context"] = {
                "type": result.get("meeting_type", "discussion"),
                "attendees": result.get("suggested_attendees", []),
                "duration": result.get("suggested_duration", 30),
                "urgency": result.get("urgency", "normal"),
                "topics": result.get("topics", [])
            }
        except json.JSONDecodeError:
            state["meeting_needed"] = False
            state["meeting_context"] = {}
        
        return state
    
    def _generate_tags(self, state: EmailProcessingState) -> EmailProcessingState:
        """Generate relevant tags for the email"""
        tags = [state["category"]]
        
        # Priority-based tags
        if state["priority"] >= 4:
            tags.append("high-priority")
        elif state["priority"] <= 2:
            tags.append("low-priority")
        
        # Content-based tags
        if state["action_items"]:
            tags.append("action-required")
        if state["meeting_needed"]:
            tags.append("meeting-request")
        if state["urgency_indicators"]:
            tags.append("urgent")
        
        # Sentiment tags
        if state["sentiment"] != "neutral":
            tags.append(f"sentiment-{state['sentiment']}")
        
        state["tags"] = list(set(tags))
        return state
    
    def _suggest_response(self, state: EmailProcessingState) -> EmailProcessingState:
        """Generate suggested response for important emails"""
        if (state["category"] in ["marketing", "notification"] or 
            state["priority"] <= 2 or 
            state["confidence"] < 0.6):
            state["suggested_response"] = None
            return state
        
        # Use personalized response prompt if available
        if 'personalized_response' in self.personalized_prompts:
            email = state["email"]
            email_context = f"Subject: {email.get('subject', '')}, Priority: {state['priority']}, Actions: {len(state['action_items'])}"
            
            response = self.llm.invoke(self.personalized_prompts['personalized_response'].format(
                email_context=email_context
            ))
            state["suggested_response"] = response.content.strip()
        else:
            # Generate simple response template
            email = state["email"]
            if state["action_items"]:
                state["suggested_response"] = f"Thank you for your email regarding '{email.get('subject', '')}'. I'll review the action items and get back to you shortly."
            elif state["meeting_needed"]:
                state["suggested_response"] = f"Thanks for reaching out. I'd be happy to discuss this further. Let me check my calendar and propose some meeting times."
            else:
                state["suggested_response"] = f"Thank you for your email. I've received your message and will respond appropriately."
        
        return state
    
    def _finalize_processing(self, state: EmailProcessingState) -> EmailProcessingState:
        """Finalize processing and set archive decision"""
        # Auto-archive decision logic
        auto_archive_categories = ["marketing", "notification", "social"]
        state["should_archive"] = (
            state["category"] in auto_archive_categories and
            state["priority"] <= 2 and
            state["confidence"] > 0.7 and
            not state["action_items"] and
            not state["meeting_needed"]
        )
        
        # Add processing metadata
        state["processing_metadata"] = {
            "workflow_version": "1.0",
            "confidence_score": state["confidence"],
            "total_action_items": len(state["action_items"]),
            "has_urgency_indicators": bool(state["urgency_indicators"]),
            "processing_timestamp": pd.Timestamp.now().isoformat()
        }
        
        return state
    
    def process_email(self, email: Dict[str, Any]) -> EmailProcessingState:
        """Process a single email through the complete workflow"""
        initial_state = EmailProcessingState(
            email=email,
            category="",
            confidence=0.0,
            priority=3,
            urgency_indicators=[],
            action_items=[],
            should_archive=False,
            meeting_needed=False,
            meeting_context={},
            tags=[],
            sentiment="neutral",
            suggested_response=None,
            processing_metadata={}
        )
        
        return self.graph.invoke(initial_state)
    
    def process_email_with_training(self, email, conversation_history, agent_context, similar_training):
        """Process email using personalized training and context"""
        
        # Add similar training examples to the context
        if similar_training:
            # This would enhance the prompts with similar examples
            pass
        
        # Process through the standard workflow but with enhanced prompts
        result = self.process_email(email)
        
        # Add training-specific metadata
        result['training_examples_used'] = len(similar_training)
        result['has_personalized_prompts'] = len(self.personalized_prompts) > 0
        
        return result