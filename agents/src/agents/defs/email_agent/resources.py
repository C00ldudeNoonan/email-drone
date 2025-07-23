# email_agent/components/email_ingestion/resources.py
from dagster import ConfigurableResource, EnvVar
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pickle
import os
import base64
from typing import List, Dict, Optional

class GmailClientResource(ConfigurableResource):
    """Gmail API client resource following dg patterns"""
    
    credentials_path: str = EnvVar("GMAIL_CREDENTIALS_PATH")
    token_path: str = EnvVar("GMAIL_TOKEN_PATH") 
    scopes: List[str] = ["https://www.googleapis.com/auth/gmail.modify"]
    
    def get_service(self):
        """Get authenticated Gmail service"""
        creds = self._get_credentials()
        return build('gmail', 'v1', credentials=creds)
    
    def _get_credentials(self):
        """Handle OAuth2 authentication"""
        creds = None
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
            else:
                from google_auth_oauthlib.flow import InstalledAppFlow
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes
                )
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds
    
    def fetch_emails(self, query: str = "is:unread", max_results: int = 50) -> List[Dict]:
        """Fetch emails from Gmail"""
        service = self.get_service()
        
        try:
            results = service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for message in messages:
                msg = service.users().messages().get(
                    userId='me', id=message['id'], format='full'
                ).execute()
                emails.append(self._parse_email(msg))
            
            return emails
            
        except Exception as e:
            raise Exception(f"Failed to fetch emails: {e}")
    
    def _parse_email(self, msg: Dict) -> Dict:
        """Parse Gmail message to structured format"""
        payload = msg['payload']
        headers = {h['name'].lower(): h['value'] for h in payload.get('headers', [])}
        
        return {
            'id': msg['id'],
            'thread_id': msg['threadId'],
            'snippet': msg['snippet'],
            'body': self._extract_body(payload),
            'labels': msg.get('labelIds', []),
            'subject': headers.get('subject', ''),
            'from_email': headers.get('from', ''),
            'to_email': headers.get('to', ''),
            'date': headers.get('date', ''),
            'internal_date': msg.get('internalDate'),
            'size_estimate': msg.get('sizeEstimate', 0)
        }
    
    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
        else:
            if payload['body'].get('data'):
                body = base64.urlsafe_b64decode(
                    payload['body']['data']
                ).decode('utf-8', errors='ignore')
        
        return body
    
    def modify_email_labels(self, email_id: str, add_labels: List[str] = None, 
                           remove_labels: List[str] = None) -> bool:
        """Modify email labels"""
        service = self.get_service()
        
        try:
            modify_request = {}
            if add_labels:
                modify_request['addLabelIds'] = add_labels
            if remove_labels:
                modify_request['removeLabelIds'] = remove_labels
            
            service.users().messages().modify(
                userId='me', id=email_id, body=modify_request
            ).execute()
            
            return True
        except Exception:
            return False