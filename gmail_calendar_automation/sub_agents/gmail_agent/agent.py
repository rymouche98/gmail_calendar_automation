from google.adk import Agent
from dotenv import load_dotenv
import os
from customer_automation_agent.tools.gmail_tool import GmailTool
from customer_automation_agent.sub_agents.gmail_agent.prompt import prompt_retriever, prompt_sender, prompt_root


load_dotenv()

app_crednitals = os.getenv('CREDENTIALS')
gmail = GmailTool(app_credentials_path=app_crednitals)

authentication_status = gmail.get_auth_status
authenticate_user = gmail.authenticate
send_email = gmail.send_email
retrieve_emails = gmail.retrieve_emails

gmail_sender_agent = Agent(
    name = 'gmail_sender_agent',
    model = os.getenv('MODEL'),
    instruction = prompt_sender,
    tools = [send_email,authenticate_user,authentication_status]
)

gmail_retriever_agent = Agent(
    name = 'gmail_retriever_agent',
    model = os.getenv('MODEL'),
    instruction = prompt_retriever,
    tools = [retrieve_emails,authenticate_user,authentication_status]
)

# Root Gmail Agent
gmail_root_agent = Agent(
    name='gmail_root_agent',
    model=os.getenv('MODEL'),
    instruction=prompt_root,
    sub_agents=[gmail_sender_agent, gmail_retriever_agent]
)