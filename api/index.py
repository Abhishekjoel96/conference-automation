from fastapi import FastAPI, HTTPException, Body, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
import sys
import json
import uvicorn
from dotenv import load_dotenv
import logging
import threading
import time

# Global dictionary to store background job status
job_status = {}

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Import modules
from src.modules.participant_scraper import get_participant_scraper
from src.modules.linkedin_research import get_linkedin_researcher
from src.modules.message_generator import get_message_generator
from src.modules.approval_tracker import get_approval_tracker
from src.modules.message_sender import get_message_sender
from src.modules.report_generator import get_report_generator
from src.modules.workflow_controller import get_workflow_controller

# Create FastAPI app
app = FastAPI(title="Conference Networking Automation API")

# Configure CORS - production-ready settings
origins = [
    "http://localhost:3000",             # Local development frontend
    "http://localhost:3001",             # Alternative local frontend port
    "http://localhost:3002",             # Alternative local frontend port
    "http://localhost:3003",             # Alternative local frontend port
    "http://127.0.0.1:8002",            # Backend port (for browser preview)
    "http://localhost:8002",            # Backend port (for browser preview)
    "https://conference-automation.vercel.app",  # Production frontend
    "https://conference-automation-*.vercel.app", # Preview deployments
    os.getenv("FRONTEND_URL", "")       # Frontend URL from environment variable
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# Define data models
class LoginCredentials(BaseModel):
    username: str
    password: str

class ParticipantBase(BaseModel):
    name: str
    role: Optional[str] = None
    country: Optional[str] = None
    company: str
    linkedin_url: Optional[str] = None
    notes: Optional[str] = None

class ScrapeRequest(BaseModel):
    event_name: str
    conference_url: str
    login_credentials: Optional[LoginCredentials] = None

class ManualInputRequest(BaseModel):
    event_name: str
    participants: List[ParticipantBase]

class MessageGenerationRequest(BaseModel):
    event_name: str
    user_name: str
    user_role: str
    user_company_name: str
    user_company_description: str
    participants: List[ParticipantBase]

class ApprovalUpdateRequest(BaseModel):
    event_name: str
    participant_name: str
    status: str = Field(..., description="Must be one of: Approved, Needs Edits, Pending")
    feedback: Optional[str] = None

class MessageSendingRequest(BaseModel):
    event_name: str
    conference_platform_url: Optional[str] = None

class ReportGenerationRequest(BaseModel):
    event_name: str
    user_name: str
    user_company_name: str
    
class LoginCredentials(BaseModel):
    username: str
    password: str

class WorkflowRequest(BaseModel):
    event_name: str
    conference_url: Optional[str] = None
    login_credentials: Optional[LoginCredentials] = None
    participants: List[ParticipantBase]
    user_name: str
    user_role: str
    user_company_name: str
    user_company_description: Optional[str] = None
    skip_research: Optional[bool] = False

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

# Define API endpoints
@app.get("/")
async def root():
    return {"message": "Conference Networking Automation API"}

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "services": {
            "proxycurl": os.getenv('PROXYCURL_API_KEY') is not None,
            "serpapi": os.getenv('SERPAPI_API_KEY') is not None,
            "openai": os.getenv('OPENAI_API_KEY') is not None,
            "google_drive": os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE') is not None
        }
    }

@app.post("/scrape")
async def scrape_participants(request: ScrapeRequest):
    """Scrape participants from a conference website."""
    scraper = get_participant_scraper()
    
    try:
        # Convert login credentials to dict if provided
        login_credentials = None
        if request.login_credentials:
            login_credentials = request.login_credentials.dict()
            
        result = scraper.scrape_participants(
            event_name=request.event_name,
            conference_url=request.conference_url,
            login_credentials=login_credentials
        )
        
        if result:
            return {"status": "success", "participants": result}
        else:
            raise HTTPException(status_code=500, detail="Failed to scrape participants")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/manual-input")
async def manual_input_participants(request: ManualInputRequest):
    """Manually input participants when scraping fails."""
    scraper = get_participant_scraper()
    
    try:
        result = scraper.fallback_manual_input(
            event_name=request.event_name,
            participants_data=json.loads(json.dumps([p.dict() for p in request.participants]))
        )
        
        if result:
            return {"status": "success", "participants": result}
        else:
            raise HTTPException(status_code=500, detail="Failed to process participants")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-messages")
async def generate_messages(request: MessageGenerationRequest):
    """Generate personalized messages for participants."""
    generator = get_message_generator()
    
    try:
        result = generator.process_participants_batch(
            event_name=request.event_name,
            participants_data=json.loads(json.dumps([p.dict() for p in request.participants])),
            user_name=request.user_name,
            user_role=request.user_role,
            user_company_name=request.user_company_name,
            user_company_description=request.user_company_description
        )
        
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/approval-status/{event_name}")
async def get_approval_status(event_name: str):
    """Get approval status for all participants."""
    tracker = get_approval_tracker()
    
    try:
        status = tracker.get_approval_status(event_name)
        return {"status": "success", "participants": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/update-approval")
async def update_approval(request: ApprovalUpdateRequest):
    """Update approval status for a participant."""
    tracker = get_approval_tracker()
    
    # Validate status
    valid_statuses = ["Approved", "Needs Edits", "Pending"]
    if request.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    try:
        result = tracker.update_participant_status(
            event_name=request.event_name,
            participant_name=request.participant_name,
            status=request.status,
            feedback=request.feedback
        )
        
        if result:
            return {"status": "success"}
        else:
            raise HTTPException(status_code=500, detail=f"Failed to update status for {request.participant_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/send-messages")
async def send_messages(request: MessageSendingRequest):
    """Simulate sending messages to approved participants."""
    sender = get_message_sender()
    
    try:
        result = sender.process_approved_messages(
            event_name=request.event_name,
            conference_platform_url=request.conference_platform_url
        )
        
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def run_workflow_in_background(job_id: str, request_dict: dict):
    """Run the workflow process in a background thread"""
    try:
        # Update job status to running
        job_status[job_id] = {
            "status": "running", 
            "progress": 0.0,
            "message": "Starting workflow process..."
        }
        
        # Get workflow controller
        workflow_controller = get_workflow_controller()
        
        # Update progress
        job_status[job_id]["progress"] = 0.1
        job_status[job_id]["message"] = "Scraping up to 10 participants from conference website..."
        
        # Convert participants data format
        participants_data = request_dict.get("participants", [])
        
        # Process login credentials
        login_credentials = request_dict.get("login_credentials")
        
        # Update progress after scraping
        job_status[job_id]["progress"] = 0.25
        job_status[job_id]["message"] = "Researching participants on LinkedIn and Web..."
        
        # Run the workflow
        result = workflow_controller.start_workflow(
            event_name=request_dict.get("event_name"),
            conference_url=request_dict.get("conference_url"),
            login_credentials=login_credentials,
            participants_data=participants_data,
            user_name=request_dict.get("user_name"),
            user_role=request_dict.get("user_role"),
            user_company_name=request_dict.get("user_company_name"),
            user_company_description=request_dict.get("user_company_description"),
            skip_research=False  # Always do full research - the user wants thorough LLM processing
        )
        
        # Update progress during message generation
        job_status[job_id]["progress"] = 0.6
        job_status[job_id]["message"] = "Generating personalized messages using LLM..."
        
        # Small delay to ensure OpenAI API calls have time to complete
        time.sleep(2)  
        
        # Update progress during Google Sheets update
        job_status[job_id]["progress"] = 0.8
        job_status[job_id]["message"] = "Updating Google Sheets with participant data and messages..."
        
        # Small delay to ensure Google API calls have time to complete
        time.sleep(2)
        
        # Update job status to complete
        job_status[job_id] = {
            "status": "completed",
            "progress": 1.0,
            "message": "Successfully processed participants and generated personalized messages. Data saved to Google Sheets and PDFs.",
            "result": result
        }
        
    except Exception as e:
        # Update job status to failed
        job_status[job_id] = {
            "status": "failed",
            "progress": 0.0,
            "message": f"Error: {str(e)}"
        }
        print(f"Background job error: {str(e)}")

@app.post("/workflow/start")
async def start_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """Start the full automation workflow in the background"""
    try:
        # Generate a unique job ID
        job_id = f"job_{int(time.time())}"
        
        # Initialize job status
        job_status[job_id] = {
            "status": "queued",
            "progress": 0.0,
            "message": "Job queued and waiting to start"
        }
        
        # Convert request to dict for thread safety
        request_dict = {
            "event_name": request.event_name,
            "conference_url": request.conference_url,
            "login_credentials": request.login_credentials.dict() if request.login_credentials else None,
            "participants": json.loads(json.dumps([p.dict() for p in request.participants])),
            "user_name": request.user_name,
            "user_role": request.user_role,
            "user_company_name": request.user_company_name,
            "user_company_description": request.user_company_description,
            "skip_research": request.skip_research
        }
        
        # Start background thread for processing
        thread = threading.Thread(target=run_workflow_in_background, args=(job_id, request_dict))
        thread.daemon = True  # This allows the thread to be terminated when the main process exits
        thread.start()
        
        return {"status": "success", "message": "Workflow started in background", "job_id": job_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the current status of a background job"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail=f"Job with ID {job_id} not found")
    
    return JobStatusResponse(
        job_id=job_id,
        status=job_status[job_id]["status"],
        progress=job_status[job_id]["progress"],
        message=job_status[job_id]["message"],
        result=job_status[job_id].get("result")
    )

@app.post("/generate-report")
async def generate_report(request: ReportGenerationRequest):
    """Generate a summary report for the event."""
    reporter = get_report_generator()
    
    try:
        result = reporter.generate_summary_report(
            event_name=request.event_name,
            user_name=request.user_name,
            user_company_name=request.user_company_name
        )
        
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Import mock data functions
from mock_data import get_events, get_participants, get_draft_messages, get_approval_status, get_sent_messages, get_summary_report

# Mock data endpoints for testing the frontend
@app.get("/api/mock/events")
def mock_get_events():
    """Get all available events (mock data)"""
    return get_events()

@app.get("/api/mock/events/{event_name}/participants")
def mock_get_participants(event_name: str):
    """Get participants for an event (mock data)"""
    return get_participants(event_name)

@app.get("/api/mock/events/{event_name}/drafts")
def mock_get_draft_messages(event_name: str):
    """Get draft messages for an event (mock data)"""
    return get_draft_messages(event_name)

@app.get("/api/mock/events/{event_name}/approval")
def mock_get_approval_status(event_name: str):
    """Get approval status for an event (mock data)"""
    return get_approval_status(event_name)

@app.get("/api/mock/events/{event_name}/sent")
def mock_get_sent_messages(event_name: str):
    """Get sent messages for an event (mock data)"""
    return get_sent_messages(event_name)

@app.get("/api/mock/events/{event_name}/report")
def mock_get_summary_report(event_name: str):
    """Get summary report for an event (mock data)"""
    return get_summary_report(event_name)

# Redirect all regular API endpoints to use mock data if ?mock=true is passed
@app.middleware("http")
async def use_mock_data_middleware(request, call_next):
    """Check for mock=true query parameter and redirect to mock endpoints"""
    if request.query_params.get("mock") == "true":
        path = request.url.path
        if path == "/api/events":
            return {"events": get_events()}
        elif "/api/events/" in path and "/participants" in path:
            event_name = path.split("/api/events/")[1].split("/participants")[0]
            return {"participants": get_participants(event_name)}
        elif "/api/events/" in path and "/drafts" in path:
            event_name = path.split("/api/events/")[1].split("/drafts")[0]
            return {"drafts": get_draft_messages(event_name)}
        elif "/api/events/" in path and "/approval" in path:
            event_name = path.split("/api/events/")[1].split("/approval")[0]
            return {"approval": get_approval_status(event_name)}
        elif "/api/events/" in path and "/sent" in path:
            event_name = path.split("/api/events/")[1].split("/sent")[0]
            return {"sent": get_sent_messages(event_name)}
        elif "/api/events/" in path and "/report" in path:
            event_name = path.split("/api/events/")[1].split("/report")[0]
            return {"report": get_summary_report(event_name)}
    
    response = await call_next(request)
    return response
    
# For local development
if __name__ == "__main__":
    uvicorn.run("index:app", host="0.0.0.0", port=8000, reload=True)
