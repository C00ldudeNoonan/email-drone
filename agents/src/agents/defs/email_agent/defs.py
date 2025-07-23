from dagster import Definitions
from .assets import (
    inbox_emails, 
    structured_emails, 
    email_training_data,
    user_feedback_data,
    personalized_email_prompts,
    processed_emails
)
from .resources import GmailClientResource, LLMClientResource

email_agent_component = Definitions(
    assets=[
        inbox_emails,
        structured_emails,
        email_training_data,
        user_feedback_data,
        personalized_email_prompts,
        processed_emails
    ],
    resources={
        "gmail_client": GmailClientResource(),
        "llm_client": LLMClientResource()
    }
)