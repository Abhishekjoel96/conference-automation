# Conference Networking Automation

A comprehensive automation system for managing conference networking, including participant scraping, research, message generation, approval tracking, and report generation, all integrated with Google Drive and Sheets.

## Features

1. **Participant Scraping**
   - Automated scraping of participant data from conference websites using Phantombuster
   - Manual participant input option for fallback scenarios

2. **LinkedIn Research**
   - Automated research on participants using Phantombuster and SerpAPI
   - Gathering additional information to personalize outreach

3. **Message Generation**
   - AI-powered personalized message creation using OpenAI
   - Identification of synergies between you and participants

4. **Approval Tracking**
   - Message review and approval workflow
   - Feedback mechanism for message improvements

5. **Message Sending Simulation**
   - Simulation of message sending with screenshots
   - Response tracking

6. **Report Generation**
   - Comprehensive summary reports in PDF format
   - Campaign metrics and analysis

7. **Google Drive Integration**
   - Automatic creation and management of Google Drive folders
   - Google Sheets for tracking participants and approvals

## System Architecture

The application is built with a modular architecture:

- **Backend**: Python-based API with FastAPI
- **Frontend**: React-based UI with Material-UI components
- **Services**: External API integrations (Google Drive, Phantombuster, SerpAPI, OpenAI)
- **Modules**: Core functionality components

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Node.js 14.x or higher
- Google API credentials
- Phantombuster API key
- SerpAPI key
- OpenAI API key

### Installation

#### Backend Setup

1. Clone the repository

```
git clone <repository-url>
cd conference_automation
```

2. Create and activate a virtual environment

```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies

```
pip install -r requirements.txt
```

4. Set up environment variables

Create a `.env` file in the root directory with the following variables:

```
# API Keys
PHANTOMBUSTER_API_KEY=your_phantombuster_api_key
SERPAPI_API_KEY=your_serpapi_key
OPENAI_API_KEY=your_openai_api_key

# Google API
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=your_redirect_uri
```

5. Run the backend server

```
python -m uvicorn api.index:app --reload
```

#### Frontend Setup

1. Navigate to the frontend directory

```
cd frontend
```

2. Install dependencies

```
npm install
```

3. Start the development server

```
npm start
```

## Usage

### CLI Usage

The application can be used via command-line interface:

```
python cli/main.py <command> [options]
```

Available commands:

- `scrape`: Scrape participants from a conference website
- `manual-input`: Manually input participants
- `generate-messages`: Generate personalized messages
- `update-approval`: Update approval status
- `list-approval`: List approval status
- `send-messages`: Simulate sending messages
- `generate-report`: Generate a summary report

For help with specific commands:

```
python cli/main.py <command> --help
```

### Web UI Usage

Navigate to http://localhost:3000 to use the web interface:

1. **Participant Input**: Add conference participants via automatic scraping or manual input
2. **Outreach Drafts**: Review generated outreach messages
3. **Message Approval**: Approve or request edits for messages
4. **Sent Messages**: Track messages that have been sent
5. **Summary**: View campaign metrics and generate reports

## API Documentation

The API documentation is available at http://localhost:8000/docs when the backend server is running.

## Deployment

### Vercel Deployment

The application is configured for deployment on Vercel:

1. Install Vercel CLI

```
npm install -g vercel
```

2. Deploy the application

```
vercel
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google API for Drive and Sheets integration
- Phantombuster for web scraping
- SerpAPI for search capabilities
- OpenAI for message generation
