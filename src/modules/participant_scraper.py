import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import services
from src.services.serpapi import get_serpapi_service
from src.services.google_drive import get_drive_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ParticipantScraper:
    def __init__(self):
        self.serpapi = get_serpapi_service()
        self.google_drive = get_drive_service()
    
    def scrape_participants(self, event_name: str, conference_url: str, search_id: str = None, login_credentials: Optional[Dict[str, str]] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Scrape participants from a conference website and store in Google Drive.
        
        Args:
            event_name: Name of the event (used for file naming)
            conference_url: URL of the conference website
            search_id: Optional parameter (not used by SerpAPI but kept for API compatibility)
            login_credentials: Optional dictionary with username and password for protected sites
            
        Returns:
            List of participant data dictionaries or None if scraping failed
        """
        if login_credentials:
            logger.info(f"Starting participant scraping for {event_name} from {conference_url} with provided credentials")
        else:
            logger.info(f"Starting participant scraping for {event_name} from {conference_url}")
        
        # Create event folders in Google Drive
        event_folders = self.google_drive.create_event_folders(event_name)
        
        # Create participants list spreadsheet
        participants_sheet_id = self.google_drive.create_participants_list(event_name)
        
        # Create approval tracker spreadsheet
        approval_tracker_id = self.google_drive.create_approval_tracking_sheet(event_name)
        
        # Scrape participants from conference website using SerpAPI
        # Note: SerpAPI doesn't need search_id but we keep the parameter for API compatibility
        participants_data = self.serpapi.scrape_conference_participants(
            conference_url=conference_url,
            search_id=search_id,  # Ignored by SerpAPI
            login_credentials=login_credentials  # Noted but ignored by SerpAPI
        )
        
        if not participants_data:
            logger.error(f"Failed to scrape participants from {conference_url}")
            return None
        
        # Format participant data for Google Sheets
        formatted_participants = []
        for participant in participants_data:
            formatted_participant = {
                'name': participant.get('name', ''),
                'role': participant.get('role', ''),
                'country': participant.get('country', ''),
                'company': participant.get('company', ''),
                'linkedin_url': participant.get('linkedin_url', ''),
                'notes': ''
            }
            formatted_participants.append(formatted_participant)
        
        # Add participants to the spreadsheet
        self.google_drive.add_participants_to_sheet(participants_sheet_id, formatted_participants)
        
        # Add participants to approval tracker
        for participant in formatted_participants:
            self.google_drive.add_participant_to_approval_tracker(
                spreadsheet_id=approval_tracker_id,
                participant_name=participant['name'],
                company_name=participant['company']
            )
        
        logger.info(f"Successfully processed {len(formatted_participants)} participants for {event_name}")
        
        # Return the participant data for further processing
        return formatted_participants
    
    def fallback_manual_input(self, event_name: str, participants_data: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
        """
        Fallback method when scraping fails - handle manually input participant data.
        
        Args:
            event_name: Name of the event (used for file naming)
            participants_data: Manually input participant data
            
        Returns:
            List of participant data dictionaries or None if processing failed
        """
        logger.info(f"Processing manually input participants for {event_name}")
        
        # Create event folders in Google Drive
        event_folders = self.google_drive.create_event_folders(event_name)
        
        # Create participants list spreadsheet
        participants_sheet_id = self.google_drive.create_participants_list(event_name)
        
        # Create approval tracker spreadsheet
        approval_tracker_id = self.google_drive.create_approval_tracking_sheet(event_name)
        
        # Format participant data for Google Sheets if needed
        formatted_participants = []
        for participant in participants_data:
            # Ensure all required fields are present
            formatted_participant = {
                'name': participant.get('name', ''),
                'role': participant.get('role', ''),
                'country': participant.get('country', ''),
                'company': participant.get('company', ''),
                'linkedin_url': participant.get('linkedin_url', ''),
                'notes': participant.get('notes', '')
            }
            formatted_participants.append(formatted_participant)
        
        # Add participants to the spreadsheet
        self.google_drive.add_participants_to_sheet(participants_sheet_id, formatted_participants)
        
        # Add participants to approval tracker
        for participant in formatted_participants:
            self.google_drive.add_participant_to_approval_tracker(
                spreadsheet_id=approval_tracker_id,
                participant_name=participant['name'],
                company_name=participant['company']
            )
        
        logger.info(f"Successfully processed {len(formatted_participants)} manually input participants for {event_name}")
        
        # Return the participant data for further processing
        return formatted_participants

# Initialize the scraper
def get_participant_scraper():
    """Get an instance of the participant scraper."""
    return ParticipantScraper()
