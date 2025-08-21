from google.adk import Agent
from dotenv import load_dotenv
import os
from gmail_calendar_automation.tools.google_calendar_tool import GoogleCalendarTool

load_dotenv()

app_credentials = os.getenv('CREDENTIALS')
google_calendar = GoogleCalendarTool(app_credentials_path=app_credentials)

authentication_status = google_calendar.get_auth_status
authenticate_user = google_calendar.authenticate
create_event = google_calendar.create_event
list_events = google_calendar.list_events
delete_event = google_calendar.delete_event

google_calendar_creator_agent = Agent(
    name='google_calendar_creator_agent',
    model=os.getenv('MODEL'),
    instruction="Create events in Google Calendar.",
    tools=[create_event, authenticate_user, authentication_status]
)

google_calendar_manager_agent = Agent(
    name='google_calendar_manager_agent',
    model=os.getenv('MODEL'),
    instruction="Manage and list events in Google Calendar.",
    tools=[list_events, delete_event, authenticate_user, authentication_status]
)

# Root Google Calendar Agent
google_calendar_root_agent = Agent(
    name='google_calendar_root_agent',
    model=os.getenv('MODEL'),
    instruction="""
    You are the root Google Calendar service agent.
    Your job is to determine whether the user's request is to:
    1. Create an event (use the google_calendar_creator_agent)
    2. Manage or list events (use the google_calendar_manager_agent)

    Instructions:
    - If the user asks to create, schedule, or add an event → forward the request to google_calendar_creator_agent.
    - If the user asks to view, list, or delete events → forward the request to google_calendar_manager_agent.
    - Always forward the user's original request without modifying meaning.
    """,
    sub_agents=[google_calendar_creator_agent, google_calendar_manager_agent]
)
