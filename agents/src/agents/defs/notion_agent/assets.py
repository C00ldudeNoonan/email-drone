from dagster import asset, AssetExecutionContext, MetadataValue, Config
from .lib.workflows import NotionWorkflow
import pandas as pd
from typing import List, Dict

class NotionAgentConfig(Config):
    """Flexible configuration for Notion intelligence agent"""
    days_back: int = 7
    min_content_length: int = 100
    include_empty_docs: bool = False
    database_priorities: Dict[str, int] = {}
    analysis_depth: str = "standard"
    max_documents_per_run: int = 100

@asset(
    group_name="notion_intelligence",
    description="Recent documents from Notion databases"
)
def recent_notion_documents(
    context: AssetExecutionContext,
    notion_client,
    config: NotionAgentConfig
) -> List[Dict]:
    """Fetch recent documents from Notion"""
    
    notion_service = notion_client.setup_for_execution(context)
    documents = notion_service.get_recent_documents(days_back=config.days_back)
    
    # Filter and prioritize documents
    prioritized_docs = []
    for doc in documents:
        if not config.include_empty_docs and doc.get("content_length", 0) < config.min_content_length:
            continue
        
        # Calculate priority score
        priority_score = 0.5
        db_name = doc.get("database", "")
        if db_name in config.database_priorities:
            priority_score += config.database_priorities[db_name] * 0.1
        
        doc['agent_priority_score'] = priority_score
        prioritized_docs.append(doc)
    
    # Sort by priority and limit
    prioritized_docs.sort(key=lambda x: x['agent_priority_score'], reverse=True)
    if len(prioritized_docs) > config.max_documents_per_run:
        prioritized_docs = prioritized_docs[:config.max_documents_per_run]
    
    context.add_output_metadata({
        "total_discovered": len(documents),
        "total_prioritized": len(prioritized_docs),
        "databases_analyzed": len(set(doc["database"] for doc in prioritized_docs))
    })
    
    return prioritized_docs

@asset(
    group_name="notion_intelligence", 
    description="AI-powered document summaries and analysis"
)
def notion_document_analysis(
    context: AssetExecutionContext,
    recent_notion_documents: List[Dict],
    llm_client,
    notion_client,
    config: NotionAgentConfig
) -> pd.DataFrame:
    """Analyze Notion documents for insights and summaries"""
    
    if not recent_notion_documents:
        return pd.DataFrame()
    
    # Get services
    llm = llm_client.setup_for_execution(context)
    notion_service = notion_client.setup_for_execution(context)
    
    # Create workflow and analyze
    workflow = NotionWorkflow(llm, notion_service)
    analysis_result = workflow.analyze_documents(recent_notion_documents)
    
    # Convert summaries to DataFrame
    summaries_data = []
    for summary in analysis_result["document_summaries"]:
        summary_record = {
            "document_id": summary["document_id"],
            "summary": summary["summary"],
            "key_topics": summary.get("key_topics", []),
            "document_type": summary.get("document_type", "unknown"),
            "confidence": summary.get("confidence", 0.5),
            "analysis_timestamp": pd.Timestamp.now()
        }
        summaries_data.append(summary_record)
    
    df = pd.DataFrame(summaries_data)
    
    if not df.empty:
        context.add_output_metadata({
            "documents_analyzed": len(df),
            "avg_confidence": round(df["confidence"].mean(), 3),
            "document_types": MetadataValue.json(df["document_type"].value_counts().to_dict())
        })
    
    return df