from dagster import Definitions
from .assets import recent_notion_documents, notion_document_analysis
from .resources import NotionClientResource, LLMClientResource  

notion_agent_component = Definitions(
    assets=[recent_notion_documents, notion_document_analysis],
    resources={
        "notion_client": NotionClientResource(),
        "llm_client": LLMClientResource()  # Shared with email agent
    }
)