from google.adk import Agent
from dotenv import load_dotenv
import os
from gmail_calendar_automation.prompt import root_agent_prompt
from gmail_calendar_automation.sub_agents.gmail_agent.agent import gmail_root_agent
from gmail_calendar_automation.sub_agents.google_calendar_agent.agent import google_calendar_root_agent

load_dotenv()

root_agent = Agent(
    name="main_root_agent",
    model=os.getenv("MODEL"),
    instruction=root_agent_prompt,
    sub_agents=[gmail_root_agent, google_calendar_root_agent]
)
