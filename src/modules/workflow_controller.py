#!/usr/bin/env python3

import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import modules
from src.modules.linkedin_research import get_linkedin_researcher
from src.modules.message_generator import get_message_generator
from src.modules.approval_tracker import get_approval_tracker
from src.modules.message_sender import get_message_sender
from src.modules.report_generator import get_report_generator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkflowController:
    """Controller for managing the entire workflow from participant input to report generation."""
    
    def __init__(self):
        self.linkedin_researcher = get_linkedin_researcher()
        self.message_generator = get_message_generator()
        self.approval_tracker = get_approval_tracker()
        self.message_sender = get_message_sender()
        self.report_generator = get_report_generator()
        
        # Initialize the participant scraper
        from src.modules.participant_scraper import get_participant_scraper
        self.participant_scraper = get_participant_scraper()
    
    def start_workflow(self, event_name: str, 
                      conference_url: str,
                      login_credentials: Optional[Dict[str, str]],
                      participants_data: List[Dict[str, Any]],
                      user_name: str,
                      user_role: str,
                      user_company_name: str,
                      user_company_description: str) -> Dict[str, Any]:
        """
        Start the full automation workflow: research, message generation, and preparation for approval.
        
        Args:
            event_name: Name of the conference or event
            conference_url: URL of the conference website
            login_credentials: Optional dictionary with username and password for the conference site
            participants_data: List of participant data with at least name, company, and preferably LinkedIn URL
            user_name: Name of the user sending messages
            user_role: Role/title of the user
            user_company_name: Name of the user's company
            user_company_description: Description of the user's company
            
        Returns:
            Dictionary with workflow status and results
        """
        logger.info(f"Starting full workflow for {event_name} with {len(participants_data)} participants")
        
        try:
            # Check if we need to fetch participants from the conference website
            if conference_url and not participants_data:
                logger.info(f"Attempting to scrape participants from conference website: {conference_url}")
                # This uses SerpAPI for conference website scraping
                
                try:
                    scraped_participants = self.participant_scraper.scrape_participants(
                        event_name=event_name,
                        conference_url=conference_url,
                        search_id=None,  # SerpAPI doesn't need this parameter, but kept for compatibility
                        login_credentials=login_credentials  # SerpAPI will note but ignore login credentials
                    )
                except Exception as e:
                    logger.error(f"Error during conference scraping: {str(e)}")
                    scraped_participants = []
                
                if scraped_participants:
                    logger.info(f"Successfully scraped {len(scraped_participants)} participants from conference website")
                    participants_data = scraped_participants
                else:
                    logger.warning("Failed to scrape participants from conference website")
                    if not participants_data:
                        return {
                            "status": "error",
                            "message": "No participants provided and failed to scrape from conference website"
                        }
            
            # Step 1: Research participants on LinkedIn using ProxyCurl
            research_results = []
            successful_research = 0
            failed_research = 0
            
            logger.info(f"Starting LinkedIn research for {len(participants_data)} participants")
            
            # Add participants to Google Sheet for tracking
            for participant in participants_data:
                try:
                    # Add to approval tracker
                    self.approval_tracker.add_participant(event_name, participant)
                except Exception as e:
                    logger.error(f"Error adding participant to approval tracker: {e}")
            
            # Research each participant
            for participant in participants_data:
                try:
                    participant_name = participant['name']
                    participant_role = participant.get('role', '')
                    participant_company = participant.get('company', '')
                    participant_linkedin = participant.get('linkedin_url', None)
                    participant_notes = participant.get('notes', '')
                    
                    # Research with ProxyCurl - no phantom ID needed
                    research_data = self.linkedin_researcher.research_participant(
                        participant_name=participant_name,
                        participant_role=participant_role,
                        participant_company=participant_company,
                        linkedin_url=participant_linkedin,
                        user_company_name=user_company_name,
                        additional_context=participant_notes
                    )
                    
                    research_summary = self.linkedin_researcher.generate_research_summary(research_data)
                    research_results.append(research_summary)
                    successful_research += 1
                    
                    logger.info(f"Successfully researched participant: {participant_name}")
                except Exception as e:
                    logger.error(f"Error researching participant {participant.get('name', 'Unknown')}: {e}")
                    failed_research += 1
            
            # Step 2: Generate personalized messages
            message_results = []
            successful_messages = 0
            failed_messages = 0
            
            logger.info(f"Generating personalized messages for {len(participants_data)} participants")
            
            for i, participant in enumerate(participants_data):
                try:
                    # Add research summary if available
                    research_summary = research_results[i] if i < len(research_results) else None
                    
                    message_result = self.message_generator.generate_message_for_participant(
                        event_name=event_name,
                        participant_data=participant,
                        user_name=user_name,
                        user_role=user_role,
                        user_company_name=user_company_name,
                        user_company_description=user_company_description
                    )
                    
                    if message_result:
                        message_results.append(message_result)
                        successful_messages += 1
                        
                        # Mark as pending in approval tracker
                        self.approval_tracker.update_participant_status(
                            event_name=event_name,
                            participant_name=participant['name'],
                            status='Pending',
                            feedback=''
                        )
                        
                        logger.info(f"Successfully generated message for: {participant['name']}")
                    else:
                        logger.error(f"Failed to generate message for: {participant['name']}")
                        failed_messages += 1
                except Exception as e:
                    logger.error(f"Error generating message for {participant.get('name', 'Unknown')}: {e}")
                    failed_messages += 1
            
            # Return workflow results
            return {
                "status": "success",
                "event_name": event_name,
                "research_stats": {
                    "successful": successful_research,
                    "failed": failed_research,
                    "total": len(participants_data)
                },
                "message_stats": {
                    "successful": successful_messages,
                    "failed": failed_messages,
                    "total": len(participants_data)
                },
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Error in workflow: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def send_approved_messages(self, event_name: str, conference_platform_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Send approved messages to participants.
        
        Args:
            event_name: Name of the event
            conference_platform_url: URL of the conference platform for sending messages (optional)
            
        Returns:
            Dictionary with sending statistics
        """
        logger.info(f"Sending approved messages for event: {event_name}")
        
        try:
            # Get approval status
            approval_status = self.approval_tracker.get_approval_status(event_name)
            
            # Filter for approved messages
            approved_participants = [p for p in approval_status if p['Status'] == 'Approved']
            
            if not approved_participants:
                logger.warning(f"No approved messages found for event: {event_name}")
                return {
                    "status": "warning",
                    "message": "No approved messages found",
                    "sent": 0,
                    "total": 0
                }
            
            logger.info(f"Found {len(approved_participants)} approved messages to send")
            
            # Send messages
            sent_count = 0
            for participant in approved_participants:
                try:
                    result = self.message_sender.send_message(
                        event_name=event_name,
                        participant_name=participant['Participant Name'],
                        conference_platform_url=conference_platform_url
                    )
                    
                    if result:
                        sent_count += 1
                        logger.info(f"Successfully sent message to: {participant['Participant Name']}")
                    else:
                        logger.error(f"Failed to send message to: {participant['Participant Name']}")
                except Exception as e:
                    logger.error(f"Error sending message to {participant['Participant Name']}: {e}")
            
            return {
                "status": "success",
                "sent": sent_count,
                "total": len(approved_participants)
            }
                
        except Exception as e:
            logger.error(f"Error sending messages: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    def generate_report(self, event_name: str, user_name: str, user_company_name: str) -> Dict[str, Any]:
        """
        Generate a summary report for the event.
        
        Args:
            event_name: Name of the event
            user_name: Name of the user
            user_company_name: Name of the user's company
            
        Returns:
            Dictionary with report information
        """
        logger.info(f"Generating summary report for event: {event_name}")
        
        try:
            report_data = self.report_generator.generate_report(
                event_name=event_name,
                user_name=user_name,
                user_company_name=user_company_name
            )
            
            if report_data:
                logger.info(f"Successfully generated report for: {event_name}")
                return {
                    "status": "success",
                    "report_url": report_data.get('report_url', ''),
                    "report_id": report_data.get('report_id', '')
                }
            else:
                logger.error(f"Failed to generate report for: {event_name}")
                return {
                    "status": "error",
                    "message": "Failed to generate report"
                }
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

# Initialize the controller
def get_workflow_controller():
    """
    Get a WorkflowController instance.
    
    Returns:
        WorkflowController instance
    """
    return WorkflowController()
