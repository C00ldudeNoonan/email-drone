# email_agent/definitions.py
from dagster import Definitions

from .email_ingestion import email_ingestion_component
from .email_processing import email_processing_component  
from .email_actions import email_actions_component
from .jobs.all_assets_job import all_assets_job
from .schedules.weekly_schedule import weekly_schedule

defs = Definitions(
    assets=[
        *email_ingestion_component.assets,
        *email_processing_component.assets,
        *email_actions_component.assets,
    ],
    resources={
        **email_ingestion_component.resources,
        **email_processing_component.resources,
        **email_actions_component.resources,
    },
    jobs=[all_assets_job],
    schedules=[weekly_schedule],
)