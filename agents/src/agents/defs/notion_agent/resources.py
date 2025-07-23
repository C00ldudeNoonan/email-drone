from dagster import ConfigurableResource, EnvVar, InitResourceContext
from notion_client import Client
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class NotionClientResource(ConfigurableResource):
    """Notion API client resource"""
    
    api_key: str = EnvVar("NOTION_API_KEY")
    database_ids: Dict[str, str] = {}
    
    def setup_for_execution(self, context: InitResourceContext) -> "NotionService":
        context.log.info("Setting up Notion client")
        return NotionService(
            api_key=self.api_key,
            database_ids=self.database_ids,
            logger=context.log
        )

class NotionService:
    def __init__(self, api_key: str, database_ids: Dict[str, str], logger):
        self.client = Client(auth=api_key)
        self.database_ids = database_ids
        self.logger = logger
    
    def get_recent_documents(self, days_back: int = 7) -> List[Dict]:
        """Get documents created/modified in the last N days"""
        since_date = datetime.now() - timedelta(days=days_back)
        since_iso = since_date.isoformat()
        
        all_documents = []
        
        for db_name, db_id in self.database_ids.items():
            try:
                response = self.client.databases.query(
                    database_id=db_id,
                    filter={
                        "or": [
                            {
                                "property": "Created time",
                                "created_time": {"after": since_iso}
                            },
                            {
                                "property": "Last edited time", 
                                "last_edited_time": {"after": since_iso}
                            }
                        ]
                    }
                )
                
                for page in response["results"]:
                    doc = self._parse_notion_page(page, db_name)
                    all_documents.append(doc)
                    
            except Exception as e:
                self.logger.error(f"Failed to query database {db_name}: {e}")
                continue
        
        return all_documents
    
    def _parse_notion_page(self, page: Dict, database_name: str) -> Dict:
        """Parse Notion page into structured format"""
        properties = page.get("properties", {})
        
        # Extract title
        title = "Untitled"
        for prop_name, prop_data in properties.items():
            if prop_data.get("type") == "title":
                title_array = prop_data.get("title", [])
                if title_array:
                    title = title_array[0].get("plain_text", "Untitled")
                break
        
        return {
            "id": page["id"],
            "title": title,
            "url": page["url"],
            "database": database_name,
            "created_time": page["created_time"],
            "last_edited_time": page["last_edited_time"],
            "properties": properties
        }
    
    def get_page_content(self, page_id: str) -> str:
        """Get the full content of a Notion page"""
        try:
            response = self.client.blocks.children.list(block_id=page_id)
            content_blocks = []
            
            for block in response["results"]:
                block_content = self._extract_block_content(block)
                if block_content:
                    content_blocks.append(block_content)
            
            return "\n".join(content_blocks)
            
        except Exception as e:
            self.logger.error(f"Failed to get content for page {page_id}: {e}")
            return ""
    
    def _extract_block_content(self, block: Dict) -> str:
        """Extract text content from a Notion block"""
        block_type = block.get("type", "")
        
        if block_type in ["paragraph", "heading_1", "heading_2", "heading_3"]:
            rich_text = block.get(block_type, {}).get("rich_text", [])
            return "".join([text.get("plain_text", "") for text in rich_text])
        
        return ""