import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import services
from ..services.google_drive import get_drive_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ApprovalTracker:
    def __init__(self):
        self.drive_service = get_drive_service()
    
    def get_approval_status(self, event_name: str) -> List[Dict[str, Any]]:
        """
        Get the current approval status for all participants.
        
        Args:
            event_name: Name of the event
            
        Returns:
            List of dictionaries with participant approval status
        """
        try:
            logger.info(f"Getting approval status for {event_name}")
            
            # Get the approval tracker spreadsheet ID
            spreadsheet_id = self._get_approval_tracker_id(event_name)
            
            if not spreadsheet_id:
                logger.error(f"Could not find approval tracker for {event_name}")
                return []
            
            # Get all data from the sheet
            result = self.drive_service.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Approval Status!A:G'
            ).execute()
            
            values = result.get('values', [])
            
            if not values or len(values) <= 1:  # Only header row or empty
                logger.warning(f"No participants found in approval tracker for {event_name}")
                return []
        except Exception as e:
            logger.error(f"Error getting approval status: {e}")
            return []
        
        # Convert to list of dictionaries
        approval_status = []
        headers = values[0]
        
        for i, row in enumerate(values):
            if i == 0:  # Skip header row
                continue
                
            # Ensure row has enough columns
            while len(row) < len(headers):
                row.append('')
            
            # Create dictionary from row
            participant_status = {}
            for j, header in enumerate(headers):
                participant_status[header] = row[j]
            
            approval_status.append(participant_status)
        
        logger.info(f"Found {len(approval_status)} participants in approval tracker")
        return approval_status
    
    def update_participant_status(self, 
                               event_name: str, 
                               participant_name: str, 
                               status: str, 
                               feedback: Optional[str] = None) -> bool:
        """
        Update the approval status for a participant.
        
        Args:
            event_name: Name of the event
            participant_name: Name of the participant
            status: New status (Approved, Needs Edits, Pending)
            feedback: Optional feedback for the participant
            
        Returns:
            Boolean indicating success or failure
        """
        logger.info(f"Updating approval status for {participant_name} to {status}")
        
        # Get the approval tracker spreadsheet ID
        spreadsheet_id = self._get_approval_tracker_id(event_name)
        
        if not spreadsheet_id:
            logger.error(f"Could not find approval tracker for {event_name}")
            return False
        
        # Update the status
        result = self.drive_service.update_approval_status(
            spreadsheet_id=spreadsheet_id,
            participant_name=participant_name,
            status=status,
            feedback=feedback
        )
        
        return result
    
    def get_approved_participants(self, event_name: str) -> List[Dict[str, Any]]:
        """
        Get a list of all approved participants.
        
        Args:
            event_name: Name of the event
            
        Returns:
            List of dictionaries with approved participant data
        """
        logger.info(f"Getting approved participants for {event_name}")
        
        # Get all participants with status
        all_participants = self.get_approval_status(event_name)
        
        # Filter for approved participants
        approved_participants = []
        for participant in all_participants:
            if participant.get('Status') == 'Approved':
                approved_participants.append(participant)
        
        logger.info(f"Found {len(approved_participants)} approved participants")
        return approved_participants
    
    def get_needs_edits_participants(self, event_name: str) -> List[Dict[str, Any]]:
        """
        Get a list of all participants that need edits.
        
        Args:
            event_name: Name of the event
            
        Returns:
            List of dictionaries with participants that need edits
        """
        logger.info(f"Getting participants that need edits for {event_name}")
        
        # Get all participants with status
        all_participants = self.get_approval_status(event_name)
        
        # Filter for participants that need edits
        needs_edits_participants = []
        for participant in all_participants:
            if participant.get('Status') == 'Needs Edits':
                needs_edits_participants.append(participant)
        
        logger.info(f"Found {len(needs_edits_participants)} participants that need edits")
        return needs_edits_participants
    
    def add_message(self, event_name: str, participant_name: str, message_data: Dict[str, Any], file_id: str) -> Dict[str, Any]:
        """
        Add a generated message to the approval tracker.
        
        Args:
            event_name: Name of the event
            participant_name: Name of the participant
            message_data: Dictionary with message data
            file_id: ID of the message file in Google Drive
            
        Returns:
            Dictionary with result status
        """
        try:
            logger.info(f"Adding message for {participant_name} to approval tracker for {event_name}")
            
            # Get the approval tracker spreadsheet ID
            spreadsheet_id = self._get_approval_tracker_id(event_name)
            
            if not spreadsheet_id:
                logger.error(f"Could not find approval tracker for {event_name}")
                return {
                    "status": "error",
                    "message": "Could not find approval tracker"
                }
            
            # Check if message already exists and update it if it does
            all_participants = self.get_approval_status(event_name)
            for participant in all_participants:
                if participant.get('Participant Name') == participant_name:
                    # Update the existing row with new message data
                    row_index = all_participants.index(participant) + 2  # +2 for header row and 0-indexing
                    
                    # Prepare the update
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    values = [[participant_name, participant.get('Company', ''), 
                              "Pending", current_date, "", "", file_id]]
                    
                    # Update the row
                    body = {
                        'values': values
                    }
                    result = self.sheets_service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=f"Approval Tracker!A{row_index}:G{row_index}",
                        valueInputOption="RAW",
                        body=body
                    ).execute()
                    
                    logger.info(f"Updated message for {participant_name} in approval tracker")
                    return {
                        "status": "success",
                        "message": "Message updated in approval tracker"
                    }
            
            # If participant doesn't exist, add a new row
            current_date = datetime.now().strftime('%Y-%m-%d')
            new_row = [
                participant_name,
                "(From message)",
                "Pending",
                current_date,
                "",
                "",
                file_id
            ]
            
            # Append the new row
            body = {
                'values': [new_row]
            }
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range="Approval Tracker!A:G",
                valueInputOption="RAW",
                insertDataOption="INSERT_ROWS",
                body=body
            ).execute()
            
            logger.info(f"Added new message for {participant_name} to approval tracker")
            return {
                "status": "success",
                "message": "Message added to approval tracker"
            }
            
        except Exception as e:
            logger.error(f"Error adding message to approval tracker: {e}")
            return {
                "status": "error",
                "message": f"Error adding message: {str(e)}"
            }
    
    def add_participant(self, event_name: str, participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a participant to the approval tracker.
        
        Args:
            event_name: Name of the event
            participant_data: Dictionary with participant data
            
        Returns:
            Dictionary with result status
        """
        try:
            logger.info(f"Adding participant {participant_data.get('name')} to approval tracker for {event_name}")
            
            # Get the approval tracker spreadsheet ID
            spreadsheet_id = self._get_approval_tracker_id(event_name)
            
            if not spreadsheet_id:
                logger.error(f"Could not find approval tracker for {event_name}")
                return {
                    "status": "error",
                    "message": "Could not find approval tracker"
                }
            
            # Check if participant already exists
            participants = self.get_approval_status(event_name)
            for participant in participants:
                if participant.get('Participant Name') == participant_data.get('name'):
                    logger.warning(f"Participant {participant_data.get('name')} already exists in approval tracker")
                    return {
                        "status": "success",
                        "message": "Participant already exists"
                    }
            
            # Prepare data for new row
            current_date = datetime.now().strftime('%Y-%m-%d')
            new_row = [
                participant_data.get('name', ''),
                participant_data.get('company', ''),
                "Pending",  # Default status
                current_date,  # Date submitted
                "",  # Date approved
                "",  # Feedback notes
                current_date   # Last updated
            ]
            
            # Get the current values
            result = self.drive_service.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='Approval Status!A:G'
            ).execute()
            
            values = result.get('values', [])
            next_row = len(values) + 1
            
            # Append the new row
            body = {
                'values': [new_row]
            }
            
            self.drive_service.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f'Approval Status!A{next_row}',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Added participant {participant_data.get('name')} to approval tracker")
            return {
                "status": "success",
                "message": "Participant added successfully"
            }
        except Exception as e:
            logger.error(f"Error adding participant to approval tracker: {e}")
            return {
                "status": "error",
                "message": f"Error adding participant: {str(e)}"
            }
    
    def _get_approval_tracker_id(self, event_name: str) -> Optional[str]:
        """
        Get the ID of the approval tracker spreadsheet.
        
        Args:
            event_name: Name of the event
            
        Returns:
            ID of the approval tracker spreadsheet or None if not found
        """
        logger.info(f"Getting approval tracker ID for {event_name}")
        spreadsheet_title = f"Message_Approval_Tracker_{event_name}"
        
        results = self.drive_service.drive_service.files().list(
            q=f"name='{spreadsheet_title}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        items = results.get('files', [])
        
        if items:
            return items[0]['id']
        else:
            # Create the approval tracker if it doesn't exist
            return self.drive_service.create_approval_tracker(event_name)
            
            
# Initialize the approval tracker
def get_approval_tracker():
    """Get an instance of the approval tracker."""
    return ApprovalTracker()
