from langchain.prompts import ChatPromptTemplate

DOCUMENT_SUMMARY_PROMPT = ChatPromptTemplate.from_template("""
Analyze this Notion document and create a comprehensive summary.

**Document Details:**
Title: {title}
Database: {database}
Content: {content}

**Analysis Framework:**
1. Main Purpose: What is this document's primary objective?
2. Key Topics: What are the main themes discussed?
3. Document Type: What type of document is this?
4. Business Impact: What business areas does this relate to?

**Return JSON Format:**
{{
    "summary": "2-3 sentence executive summary",
    "key_topics": ["topic1", "topic2", "topic3"],
    "document_type": "meeting_notes/strategy/project_plan/other",
    "business_areas": ["engineering", "marketing", "sales"],
    "confidence": 0.85
}}
""")

TREND_ANALYSIS_PROMPT = ChatPromptTemplate.from_template("""
Analyze trends across this collection of Notion documents.

**Document Collection:**
Total Documents: {total_documents}
Common Topics: {common_topics}

**Provide Analysis:**
{{
    "trending_topics": ["topic1", "topic2"],
    "document_velocity": "low/moderate/high",
    "focus_areas": ["area1", "area2"],
    "recommendations": ["rec1", "rec2"]
}}
""")