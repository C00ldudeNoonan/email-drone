from langchain.prompts import ChatPromptTemplate

# Optimized prompts for Gemini API
EMAIL_CATEGORIZATION_PROMPT = ChatPromptTemplate.from_template("""
You are an expert email analyst. Categorize this email with high accuracy and provide confidence scoring.

**Email Categories:**
- work: Professional communication requiring attention
- personal: Personal correspondence  
- marketing: Newsletters, promotions, sales outreach, unsubscribe links
- notification: System alerts, automated messages, receipts, confirmations
- meeting_request: Meeting invitations, calendar invites, scheduling requests
- action_required: Emails explicitly requesting specific actions or decisions
- support: Customer service, technical support, help desk communications
- social: Social media notifications, community updates, forum posts
- spam: Obvious spam, phishing attempts, suspicious content

**Analysis Context:**
Subject: {subject}
From: {from_email}
Sender Domain: {sender_domain}
Content Preview: {content}

**Analysis Criteria:**
1. Sender domain reputation and type (corporate, personal, automated)
2. Subject line patterns and keywords
3. Content structure and language patterns
4. Presence of automated signatures or unsubscribe links
5. Call-to-action patterns

Respond in JSON format only:
{{
    "category": "category_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation focusing on key indicators that led to this categorization"
}}
""")

PRIORITY_ASSESSMENT_PROMPT = ChatPromptTemplate.from_template("""
Assess email priority using contextual analysis. Consider both explicit and implicit urgency signals.

**Priority Scale:**
1 = Very Low (newsletters, automated notifications, can wait weeks)
2 = Low (non-urgent updates, FYI emails, can wait days)
3 = Medium (normal business communication, 24-48 hour response)
4 = High (important requests, same-day response needed)
5 = Urgent (emergency, time-sensitive, immediate attention required)

**Email Context:**
Category: {category}
Subject: {subject}
From: {from_email}
Content: {content}
Email Length: {body_length} characters

**Priority Indicators to Consider:**
- Explicit urgency words (urgent, ASAP, emergency, deadline)
- Sender relationship and authority level
- Time-sensitive keywords and phrases
- Meeting requests with specific dates
- Deadline mentions and date references
- Response expectations set in content
- Business impact implications

**Special Considerations:**
- Marketing emails are typically priority 1-2
- Automated notifications are usually priority 1-2
- Work emails from managers/clients often priority 3-4
- Meeting requests with near-term dates are priority 4+
- Emergency or system alerts should be priority 5

Return only a single number (1-5) representing the priority level.
""")

ACTION_EXTRACTION_PROMPT = ChatPromptTemplate.from_template("""
Extract actionable tasks from this email. Focus on specific, concrete actions that require human intervention.

**Email Content:**
Subject: {subject}
Body: {content}

**Action Item Criteria:**
- Must be specific and concrete (not vague suggestions)
- Should have a clear deliverable or outcome
- Must require human decision or action
- Can be completed by the email recipient
- Should include any mentioned deadlines or timeframes

**Action Item Structure:**
For each action, determine:
1. What specifically needs to be done?
2. Any deadline or timeframe mentioned?
3. Estimated effort level (low/medium/high)
4. Any dependencies or context needed?

**Examples of Good Action Items:**
- "Review and approve Q3 budget proposal by Friday 3 PM"
- "Schedule follow-up meeting with John and Sarah about project timeline"
- "Update client contract terms and send to legal team by EOD"
- "Provide feedback on draft presentation slides before tomorrow's meeting"

**Not Action Items:**
- General statements like "let me know if you have questions"
- Informational updates that don't require action
- Automated notifications or confirmations

Return JSON array:
[
    {{
        "description": "specific action description",
        "deadline": "extracted deadline or null",
        "estimated_effort": "low/medium/high",
        "context": "additional context if relevant",
        "priority": "high/medium/low"
    }}
]

If no actionable items found, return: []
""")

MEETING_DETECTION_PROMPT = ChatPromptTemplate.from_template("""
Analyze this email to determine if it requires or suggests scheduling a meeting or call.

**Email Details:**
Subject: {subject}
Content: {content}
From: {from_email}

**Meeting Indicators to Look For:**
- Direct meeting requests ("let's meet", "schedule a call", "hop on a call")
- Complex topics that would benefit from real-time discussion
- Multiple stakeholders mentioned who need to align
- Decision-making processes requiring group input
- Project planning or strategy discussions
- Problem-solving that needs collaborative thinking
- Follow-up discussions from previous meetings

**Meeting Context Analysis:**
- What type of meeting would be most appropriate?
- Who should be involved based on the content?
- What's the suggested duration based on topic complexity?
- How urgent is the meeting need?
- What are the main topics to be discussed?

**Meeting Types:**
- planning: Project planning, roadmap discussions
- review: Progress reviews, retrospectives
- discussion: General discussion, brainstorming
- decision: Decision-making, approval processes
- sync: Status updates, alignment meetings
- presentation: Demos, presentations, training

Return JSON format:
{{
    "needs_meeting": true/false,
    "meeting_type": "planning/review/discussion/decision/sync/presentation",
    "suggested_attendees": ["email1@domain.com", "email2@domain.com"],
    "suggested_duration": 30,
    "urgency": "low/normal/high",
    "topics": ["topic1", "topic2", "topic3"],
    "reasoning": "explanation of why meeting is or isn't needed"
}}
""")

PERSONALIZED_CATEGORIZATION_PROMPT = ChatPromptTemplate.from_template("""
You are a personalized email categorization agent trained on this user's specific patterns.

**User Training Examples:**
{training_examples}

**User Feedback Insights:**
{feedback_insights}

**User Custom Rules:**
- VIP Senders: {vip_senders}
- Auto-archive senders: {auto_archive_senders}
- Custom category rules: {custom_rules}

**Email to Categorize:**
Subject: {subject}
From: {from_email}
Content: {content}

Based on the user's patterns above, categorize this email and explain your reasoning by referencing similar examples.

Return JSON:
{{
    "category": "category_name",
    "confidence": 0.95,
    "reasoning": "explanation referencing user patterns and examples",
    "training_applied": true/false
}}
""")