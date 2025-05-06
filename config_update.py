import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and External Services Settings
PROXYCURL_API_KEY = os.getenv('PROXYCURL_API_KEY')
# SerpAPI is used for conference website scraping
# No additional configuration needed beyond SERPAPI_API_KEY
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Google API Settings
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'credentials/service_account.json')

# Application Settings
MAIN_FOLDER_NAME = 'Conference Outreach Automation'
OUTREACH_DRAFTS_FOLDER = 'Outreach_Drafts'
SENT_MESSAGES_FOLDER = 'Sent_Messages_Log'
SUMMARY_REPORTS_FOLDER = 'Summary_Reports'

# Message Templates
COMPANY_DESCRIPTION_TEMPLATE = """
{company_name} is {company_description}
"""

MESSAGE_TEMPLATE = """
Hi {participant_name},

I'm {user_name} from {company_name}. {company_short_description}

{personalized_intro}

{synergy_point}

Would love to explore a quick 15-min call during or after the event.

Looking forward to connecting.

Warm regards,
{user_name}
{user_role}, {company_name}
"""
