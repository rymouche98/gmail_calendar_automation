import os
import json
from typing import Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError


class GoogleCalendarTool:
    """Tool for Google Calendar operations designed for AI agent use."""

    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, app_credentials_path: str, user_token_path: str = os.getenv('TOKEN')):
        """
        Initialize Google Calendar tool.

        Args:
            user_token_path: Path to user token JSON file
            app_credentials_path: Path to app credentials JSON file
        """
        self.user_token_path = user_token_path
        self.app_credentials_path = app_credentials_path
        self._credentials = None
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load credentials from token file if available."""
        try:
            self._credentials = Credentials.from_authorized_user_file(
                self.user_token_path, self.SCOPES
            )
        except (FileNotFoundError, json.JSONDecodeError):
            self._credentials = None

    def _save_credentials(self, credentials: Credentials) -> None:
        """Save credentials to token file."""
        with open(self.user_token_path, 'w') as token_file:
            token_file.write(credentials.to_json())

    def _ensure_valid_credentials(self) -> bool:
        """Ensure credentials are valid and refresh if needed."""
        if not self._credentials:
            return False

        if self._credentials.expired and self._credentials.refresh_token:
            try:
                self._credentials.refresh(Request())
                self._save_credentials(self._credentials)
                return True
            except RefreshError:
                return False

        return not self._credentials.expired

    def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Google OAuth.

        Returns:
            Dict with success status and message
        """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.app_credentials_path, scopes=self.SCOPES
            )
            credentials = flow.run_local_server(port=0)
            self._credentials = credentials
            self._save_credentials(credentials)

            return {
                "success": True,
                "message": "Successfully authenticated with Google Calendar"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Authentication failed: {str(e)}"
            }

    def get_auth_status(self) -> Dict[str, Any]:
        """
        Check current authentication status.

        Returns:
            Dict with authentication status details
        """
        if not self._credentials:
            return {
                "authenticated": False,
                "valid": False,
                "message": "No credentials found. Please authenticate first."
            }

        has_refresh_token = bool(self._credentials.refresh_token)
        is_valid = self._ensure_valid_credentials()
        is_expired = self._credentials.expired

        return {
            "authenticated": True,
            "valid": is_valid,
            'expired': is_expired,
            "has_refresh_token": has_refresh_token,
            "message": "Ready to access calendar" if is_valid else "Authentication required"
        }

    def create_event(self, calendar_id: str, event: Dict[str, Any], send_notifications: bool = True) -> Dict[str, Any]:
        """
        Create an event in Google Calendar.

        Args:
            calendar_id: ID of the calendar where the event will be created.
            event: Event details as a dictionary.
            send_notifications: Whether to send notifications about the event creation.

        Returns:
            Dict with operation result.
        """
        if not self._ensure_valid_credentials():
            return {
                "success": False,
                "message": "Authentication required. Please call authenticate() first.",
                "error_code": "AUTH_REQUIRED"
            }

        try:
            service = build("calendar", "v3", credentials=self._credentials)
            created_event = service.events().insert(
                calendarId=calendar_id, body=event, sendNotifications=send_notifications
            ).execute()

            return {
                "success": True,
                "event_id": created_event.get("id"),
                "html_link": created_event.get("htmlLink"),
                "message": "Event created successfully."
            }

        except HttpError as e:
            return {
                "success": False,
                "message": f"Google Calendar API error: {e.reason}",
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "error_code": "UNKNOWN_ERROR"
            }

    def list_events(self, calendar_id: str, max_results: int = 10, time_min: Optional[str] = None, time_max: Optional[str] = None) -> Dict[str, Any]:
        """
        List upcoming events from Google Calendar.

        Args:
            calendar_id: ID of the calendar to retrieve events from.
            max_results: Maximum number of events to retrieve.
            time_min: The start time to filter events (ISO 8601 format). Defaults to today.
            time_max: The end time to filter events (ISO 8601 format).

        Returns:
            Dict with success status and list of events.
        """
        from datetime import datetime, timezone

        if time_min is None:
            time_min = datetime.now(timezone.utc).isoformat()

        if not self._ensure_valid_credentials():
            return {
                "success": False,
                "message": "Authentication required. Please call authenticate() first.",
                "error_code": "AUTH_REQUIRED"
            }

        try:
            service = build("calendar", "v3", credentials=self._credentials)
            events_result = service.events().list(
                calendarId=calendar_id,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
                timeMin=time_min,
                timeMax=time_max
            ).execute()

            events = events_result.get("items", [])

            return {
                "success": True,
                "events": events,
                "message": f"Retrieved {len(events)} events."
            }

        except HttpError as e:
            return {
                "success": False,
                "message": f"Google Calendar API error: {e.reason}",
                "error_code": e.resp.status
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}",
                "error_code": "UNKNOWN_ERROR"
            }

    def delete_event(self, calendar_id: str, event_id: str) -> Dict[str, Any]:
        """
        Delete an event from Google Calendar.

        Args:
            calendar_id: ID of the calendar containing the event.
            event_id: ID of the event to delete.

        Returns:
            Dict with operation result.
        """
        if not self._ensure_valid_credentials():
            return {
                "success": False,
                "message": "Authentication required. Please call authenticate() first."
            }

        try:
            service = build("calendar", "v3", credentials=self._credentials)
            service.events().delete(calendarId=calendar_id, eventId=event_id).execute()

            return {
                "success": True,
                "message": "Event deleted successfully."
            }

        except HttpError as e:
            return {
                "success": False,
                "message": f"Google Calendar API error: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }
