from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any
from .prompts import DOCUMENT_SUMMARY_PROMPT, TREND_ANALYSIS_PROMPT
import json
import pandas as pd

class NotionAnalysisState(TypedDict):
    """State for Notion document analysis workflow"""
    documents: List[Dict[str, Any]]
    document_summaries: List[Dict[str, Any]]
    trend_insights: Dict[str, Any]
    processing_metadata: Dict[str, Any]

class NotionWorkflow:
    """LangGraph workflow for Notion document intelligence"""
    
    def __init__(self, llm_client, notion_service):
        self.llm = llm_client
        self.notion_service = notion_service
        self.graph = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the Notion analysis workflow"""
        workflow = StateGraph(NotionAnalysisState)
        
        workflow.add_node("enrich_documents", self._enrich_document_content)
        workflow.add_node("summarize_documents", self._summarize_documents)
        workflow.add_node("analyze_trends", self._analyze_trends)
        workflow.add_node("finalize", self._finalize_analysis)
        
        workflow.set_entry_point("enrich_documents")
        workflow.add_edge("enrich_documents", "summarize_documents")
        workflow.add_edge("summarize_documents", "analyze_trends")
        workflow.add_edge("analyze_trends", "finalize")
        workflow.add_edge("finalize", END)
        
        return workflow.compile()
    
    def _enrich_document_content(self, state: NotionAnalysisState) -> NotionAnalysisState:
        """Enrich documents with full content"""
        enriched_docs = []
        
        for doc in state["documents"]:
            try:
                full_content = self.notion_service.get_page_content(doc["id"])
                enriched_doc = doc.copy()
                enriched_doc["full_content"] = full_content
                enriched_doc["content_length"] = len(full_content)
                enriched_docs.append(enriched_doc)
            except Exception:
                enriched_doc = doc.copy()
                enriched_doc["full_content"] = ""
                enriched_doc["content_length"] = 0
                enriched_docs.append(enriched_doc)
        
        state["documents"] = enriched_docs
        return state
    
    def _summarize_documents(self, state: NotionAnalysisState) -> NotionAnalysisState:
        """Create summaries for each document"""
        summaries = []
        
        for doc in state["documents"]:
            try:
                response = self.llm.invoke(DOCUMENT_SUMMARY_PROMPT.format(
                    title=doc["title"],
                    database=doc["database"],
                    content=doc["full_content"][:2000]
                ))
                
                summary_data = json.loads(response.content)
                summary_data["document_id"] = doc["id"]
                summaries.append(summary_data)
                
            except Exception:
                summary = {
                    "document_id": doc["id"],
                    "summary": f"Document: {doc['title']}",
                    "key_topics": [],
                    "document_type": "unknown",
                    "confidence": 0.2
                }
                summaries.append(summary)
        
        state["document_summaries"] = summaries
        return state
    
    def _analyze_trends(self, state: NotionAnalysisState) -> NotionAnalysisState:
        """Analyze trends across documents"""
        try:
            all_topics = []
            for summary in state["document_summaries"]:
                all_topics.extend(summary.get("key_topics", []))
            
            response = self.llm.invoke(TREND_ANALYSIS_PROMPT.format(
                total_documents=len(state["documents"]),
                common_topics=list(set(all_topics))[:10]
            ))
            
            trend_data = json.loads(response.content)
            state["trend_insights"] = trend_data
            
        except Exception:
            state["trend_insights"] = {
                "trending_topics": [],
                "document_velocity": "moderate",
                "focus_areas": [],
                "recommendations": []
            }
        
        return state
    
    def _finalize_analysis(self, state: NotionAnalysisState) -> NotionAnalysisState:
        """Finalize the analysis with metadata"""
        state["processing_metadata"] = {
            "total_documents_analyzed": len(state["documents"]),
            "successful_summaries": len(state["document_summaries"]),
            "analysis_timestamp": pd.Timestamp.now().isoformat()
        }
        
        return state
    
    def analyze_documents(self, documents: List[Dict[str, Any]]) -> NotionAnalysisState:
        """Analyze a collection of Notion documents"""
        initial_state = NotionAnalysisState(
            documents=documents,
            document_summaries=[],
            trend_insights={},
            processing_metadata={}
        )
        
        return self.graph.invoke(initial_state)