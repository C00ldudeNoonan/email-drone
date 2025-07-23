from dagster import Definitions
from .assets import daily_calendar_events, daily_schedule_summary
from .resources import CalendarClientResource, LLMClientResource

calendar_agent_component = Definitions(
    assets=[daily_calendar_events, daily_schedule_summary],
    resources={
        "calendar_client": CalendarClientResource(),
        "llm_client": LLMClientResource()  # Shared with other agents
    }
)