import base64
import json
import os
from email.message import EmailMessage
from typing import Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError


class GmailTool:
    """Tool for Gmail operations designed for AI agent use."""

    SCOPES = ["https://www.googleapis.com/auth/gmail.send", "https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(self, app_credentials_path: str, user_token_path:str = os.getenv('TOKEN')):
        """
        Initialize Gmail tool.

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
                "message": "Successfully authenticated with Gmail"
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
            'expired' : is_expired,
            "has_refresh_token": has_refresh_token,
            "message": "Ready to send emails" if is_valid else "Authentication required"
        }

    def send_email(self,
                   to: str,
                   subject: str,
                   content: str,
                   from_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Send an email via Gmail.

        Args:
            to: Recipient email address
            subject: Email subject
            content: Email content/body
            from_email: Sender email (optional, uses authenticated user's email)

        Returns:
            Dict with operation result
        """
        # Validate inputs
        if not to or not subject or not content:
            return {
                "success": False,
                "message": "Missing required fields: to, subject, and content are required"
            }

        # ✅ CHECK TOKEN STATUS - This validates and refreshes if needed!
        if not self._ensure_valid_credentials():
            return {
                "success": False,
                "message": "Authentication required. Please call authenticate() first."
            }

        try:
            # Build Gmail service
            service = build("gmail", "v1", credentials=self._credentials)

            # Create email message
            message = EmailMessage()
            message.set_content(content)
            message["To"] = to
            if from_email:
                message["From"] = from_email
            message["Subject"] = subject

            # Encode and send
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            result = service.users().messages().send(
                userId="me",
                body=create_message
            ).execute()

            return {
                "success": True,
                "message_id": result.get("id"),
                "message": f"Email sent successfully to {to}"
            }

        except HttpError as e:
            error_msg = f"Gmail API error: {str(e)}"
            if e.resp.status == 401:
                error_msg = "Authentication expired. Please re-authenticate."
            elif e.resp.status == 403:
                error_msg = "Insufficient permissions. Check Gmail API access."

            return {
                "success": False,
                "message": error_msg
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }

    def retrieve_emails(self, max_results: int = 10, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve recent emails from Gmail.

        Args:
            max_results: Maximum number of emails to retrieve.
            query: Gmail search query (e.g., 'is:unread', 'from:example@gmail.com').

        Returns:
            Dict with success status and list of emails.
        """
        # ✅ Ensure credentials are valid
        if not self._ensure_valid_credentials():
            return {
                "success": False,
                "message": "Authentication required. Please call authenticate() first."
            }

        try:
            service = build("gmail", "v1", credentials=self._credentials)

            # 📩 List messages
            results = service.users().messages().list(
                userId="me",
                maxResults=max_results,
                q=query
            ).execute()

            messages = results.get("messages", [])
            if not messages:
                return {
                    "success": True,
                    "emails": [],
                    "message": "No messages found."
                }

            emails = []
            for msg in messages:
                msg_data = service.users().messages().get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"]
                ).execute()

                headers = {h["name"]: h["value"] for h in msg_data["payload"]["headers"]}
                emails.append({
                    "id": msg["id"],
                    "from": headers.get("From"),
                    "subject": headers.get("Subject"),
                    "date": headers.get("Date")
                })

            return {
                "success": True,
                "emails": emails,
                "message": f"Retrieved {len(emails)} messages."
            }

        except HttpError as e:
            error_msg = f"Gmail API error: {str(e)}"
            if e.resp.status == 401:
                error_msg = "Authentication expired. Please re-authenticate."
            elif e.resp.status == 403:
                error_msg = "Insufficient permissions. Check Gmail API access."
            return {
                "success": False,
                "message": error_msg
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error: {str(e)}"
            }

    def get_mail_info(self):
            pass

    def arrange_mails(self):
            pass

    def delete_mails(self):
            pass

    def create_drafts(self):
            pass