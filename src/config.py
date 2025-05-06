import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
PROXYCURL_API_KEY = os.getenv('PROXYCURL_API_KEY')
SERPAPI_API_KEY = os.getenv('SERPAPI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Google Drive service account
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'credentials/service_account.json')

# Other configuration settings
OUTPUT_DIR = 'output'
LOG_DIR = 'logs'

# Ensure output directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'draft_messages'), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'approval_trackers'), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'sent_messages'), exist_ok=True)
os.makedirs(os.path.join(OUTPUT_DIR, 'summary_reports'), exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Google Drive folder structure
MAIN_FOLDER_NAME = 'Conference Automation'
OUTREACH_DRAFTS_FOLDER = 'Outreach Drafts'
SENT_MESSAGES_FOLDER = 'Sent Messages'
SUMMARY_REPORTS_FOLDER = 'Summary Reports'

# OpenAI templates
COMPANY_DESCRIPTION_TEMPLATE = """Please provide a concise description of {company_name} based on the information below:

{company_info}

Focus on what they do, their industry, and any noteworthy aspects."""

MESSAGE_TEMPLATE = """Please write a personalized outreach message to {participant_name} who works at {company_name}.

Participant info:
{participant_info}

Company description:
{company_description}

The message should be friendly, professional, and highlight why we're interested in connecting based on their background."""
