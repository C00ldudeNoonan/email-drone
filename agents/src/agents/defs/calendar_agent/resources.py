from dagster import ConfigurableResource, EnvVar, InitResourceContext
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import pickle
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class CalendarClientResource(ConfigurableResource):
    """Google Calendar API client resource"""
    
    credentials_path: str = EnvVar("CALENDAR_CREDENTIALS_PATH")
    token_path: str = EnvVar("CALENDAR_TOKEN_PATH")
    scopes: List[str] = ["https://www.googleapis.com/auth/calendar.readonly"]
    
    def setup_for_execution(self, context: InitResourceContext) -> "CalendarService":
        context.log.info("Setting up Calendar client")
        return CalendarService(
            credentials_path=self.credentials_path,
            token_path=self.token_path,
            scopes=self.scopes,
            logger=context.log
        )

class CalendarService:
    def __init__(self, credentials_path: str, token_path: str, scopes: List[str], logger):
        self.logger = logger
        self.service = self._authenticate(credentials_path, token_path, scopes)
    
    def _authenticate(self, credentials_path: str, token_path: str, scopes: List[str]):
        """Authenticate with Google Calendar API"""
        creds = None
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
            else:
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
                creds = flow.run_local_server(port=0)
            
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('calendar', 'v3', credentials=creds)
    
    def get_daily_events(self, target_date: datetime = None) -> List[Dict]:
        """Get events for a specific day"""
        if not target_date:
            target_date = datetime.now()
        
        start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        try:
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat() + 'Z',
                timeMax=end_of_day.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            parsed_events = []
            
            for event in events:
                parsed_event = self._parse_calendar_event(event)
                parsed_events.append(parsed_event)
            
            return parsed_events
            
        except Exception as e:
            self.logger.error(f"Failed to fetch calendar events: {e}")
            return []
    
    def _parse_calendar_event(self, event: Dict) -> Dict:
        """Parse Google Calendar event into structured format"""
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        attendees = []
        if 'attendees' in event:
            attendees = [
                {
                    'email': attendee.get('email', ''),
                    'name': attendee.get('displayName', ''),
                    'response_status': attendee.get('responseStatus', 'needsAction')
                }
                for attendee in event['attendees']
            ]
        
        return {
            'id': event['id'],
            'title': event.get('summary', 'No Title'),
            'description': event.get('description', ''),
            'start_time': start,
            'end_time': end,
            'location': event.get('location', ''),
            'attendees': attendees,
            'attendee_count': len(attendees),
            'organizer': event.get('organizer', {}).get('email', ''),
            'status': event.get('status', 'confirmed'),
            'event_type': self._classify_event_type(event.get('summary', ''))
        }
    
    def _classify_event_type(self, title: str) -> str:
        """Classify the type of calendar event"""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['1:1', 'one on one', 'sync']):
            return '1:1'
        elif any(word in title_lower for word in ['standup', 'daily', 'scrum']):
            return 'standup'
        elif any(word in title_lower for word in ['review', 'demo']):
            return 'review'
        elif any(word in title_lower for word in ['interview', 'hiring']):
            return 'interview'
        else:
            return 'meeting'