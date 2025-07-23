from dagster import define_asset_job, AssetSelection

# Individual agent jobs
email_processing_job = define_asset_job(
    name="email_processing_job",
    description="Complete email processing pipeline",
    selection=AssetSelection.groups("email_ingestion", "email_processing", "email_training")
)

notion_intelligence_job = define_asset_job(
    name="notion_intelligence_job",
    description="Notion document analysis and trend reporting",
    selection=AssetSelection.groups("notion_intelligence")
)

calendar_analysis_job = define_asset_job(
    name="calendar_analysis_job", 
    description="Calendar analysis and schedule optimization",
    selection=AssetSelection.groups("calendar_intelligence")
)