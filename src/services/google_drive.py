import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Import config settings
from ..config import (
    GOOGLE_SERVICE_ACCOUNT_FILE,
    MAIN_FOLDER_NAME,
    OUTREACH_DRAFTS_FOLDER,
    SENT_MESSAGES_FOLDER,
    SUMMARY_REPORTS_FOLDER
)


class GoogleDriveService:
    def __init__(self):
        self.credentials = self._get_credentials()
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
        self.main_folder_id = self._get_or_create_main_folder()
        self.folder_ids = self._setup_folder_structure()
    
    def _get_credentials(self):
        """Load service account credentials."""
        try:
            return service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=['https://www.googleapis.com/auth/drive', 
                        'https://www.googleapis.com/auth/spreadsheets']
            )
        except Exception as e:
            print(f"Error loading Google credentials: {e}")
            raise
    
    def _get_sheet_id(self, spreadsheet_id, sheet_name):
        """Get the sheet ID for a given sheet name in a spreadsheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            sheet_name: The name of the sheet
            
        Returns:
            The sheet ID or None if not found
        """
        try:
            # Get sheet information
            sheets_metadata = self.sheets_service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            # Find the sheet ID
            for sheet in sheets_metadata.get('sheets', []):
                if sheet.get('properties', {}).get('title') == sheet_name:
                    return sheet.get('properties', {}).get('sheetId')
            
            return None
        except Exception as e:
            print(f"Error getting sheet ID: {e}")
            return 0  # Default fallback
    
    def _get_or_create_main_folder(self):
        """Get or create the main folder."""
        results = self.drive_service.files().list(
            q=f"name='{MAIN_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        items = results.get('files', [])
        
        if items:
            print(f"Main folder '{MAIN_FOLDER_NAME}' already exists")
            return items[0]['id']
        
        # Create the main folder
        file_metadata = {
            'name': MAIN_FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        file = self.drive_service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        print(f"Created main folder '{MAIN_FOLDER_NAME}'")
        return file.get('id')
    
    def _setup_folder_structure(self):
        """Set up the folder structure for the project."""
        folder_ids = {}
        
        # Create the three main subfolders if they don't exist
        for folder_name in [OUTREACH_DRAFTS_FOLDER, SENT_MESSAGES_FOLDER, SUMMARY_REPORTS_FOLDER]:
            # Check if folder exists
            results = self.drive_service.files().list(
                q=f"name='{folder_name}' and '{self.main_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                folder_ids[folder_name] = items[0]['id']
                print(f"Folder '{folder_name}' already exists")
            else:
                # Create folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.main_folder_id]
                }
                
                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                folder_ids[folder_name] = folder.get('id')
                print(f"Created folder '{folder_name}'")
        
        return folder_ids
    
    def create_event_folders(self, event_name):
        """Create event-specific folders."""
        event_folders = {}
        
        # Create event-specific folders in Outreach Drafts and Sent Messages
        for base_folder, folder_name in [
            (OUTREACH_DRAFTS_FOLDER, f"Outreach_Drafts_{event_name}"),
            (SENT_MESSAGES_FOLDER, f"Sent_Messages_Log_{event_name}")
        ]:
            # Check if folder exists
            results = self.drive_service.files().list(
                q=f"name='{folder_name}' and '{self.folder_ids[base_folder]}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false",
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            items = results.get('files', [])
            
            if items:
                event_folders[folder_name] = items[0]['id']
                print(f"Event folder '{folder_name}' already exists")
            else:
                # Create folder
                folder_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.folder_ids[base_folder]]
                }
                
                folder = self.drive_service.files().create(
                    body=folder_metadata,
                    fields='id'
                ).execute()
                
                event_folders[folder_name] = folder.get('id')
                print(f"Created event folder '{folder_name}'")
        
        return event_folders
    
    def create_participants_list(self, event_name):
        """Create a Google Sheet for participants list."""
        spreadsheet_title = f"Participants_List_{event_name}"
        
        # Check if the spreadsheet already exists
        results = self.drive_service.files().list(
            q=f"name='{spreadsheet_title}' and '{self.main_folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        items = results.get('files', [])
        
        if items:
            print(f"Participants list '{spreadsheet_title}' already exists")
            return items[0]['id']
        
        # Create a new spreadsheet
        spreadsheet_body = {
            'properties': {'title': spreadsheet_title},
            'sheets': [{
                'properties': {
                    'title': 'Participants',
                    'gridProperties': {
                        'frozenRowCount': 1,
                        'frozenColumnCount': 0
                    }
                }
            }]
        }
        
        spreadsheet = self.sheets_service.spreadsheets().create(
            body=spreadsheet_body
        ).execute()
        
        spreadsheet_id = spreadsheet['spreadsheetId']
        
        # Move the file to the main folder
        file = self.drive_service.files().get(
            fileId=spreadsheet_id,
            fields='parents'
        ).execute()
        
        previous_parents = ",".join(file.get('parents'))
        
        self.drive_service.files().update(
            fileId=spreadsheet_id,
            addParents=self.main_folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        
        # Add headers
        values = [
            ['Full Name', 'Role/Designation', 'Country', 'Company Name', 'LinkedIn URL', 'Notes']
        ]
        
        body = {
            'values': values
        }
        
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Participants!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Format headers
        requests = [{
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.83,
                            'green': 0.83,
                            'blue': 0.83
                        },
                        'textFormat': {
                            'bold': True
                        },
                        'horizontalAlignment': 'CENTER'
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
            }
        }]
        
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        print(f"Created participants list: {spreadsheet_title}")
        return spreadsheet_id
    
    def create_approval_tracker(self, event_name):
        """Create a Google Sheet for message approval tracking."""
        spreadsheet_title = f"Message_Approval_Tracker_{event_name}"
        
        # Check if the spreadsheet already exists
        results = self.drive_service.files().list(
            q=f"name='{spreadsheet_title}' and '{self.main_folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        items = results.get('files', [])
        
        if items:
            print(f"Approval tracker '{spreadsheet_title}' already exists")
            return items[0]['id']
        
        # Create a new spreadsheet
        spreadsheet_body = {
            'properties': {'title': spreadsheet_title},
            'sheets': [{
                'properties': {
                    'title': 'Approval Status',
                    'gridProperties': {
                        'frozenRowCount': 1,
                        'frozenColumnCount': 0
                    }
                }
            }]
        }
        
        spreadsheet = self.sheets_service.spreadsheets().create(
            body=spreadsheet_body
        ).execute()
        
        spreadsheet_id = spreadsheet['spreadsheetId']
        
        # Move the file to the main folder
        file = self.drive_service.files().get(
            fileId=spreadsheet_id,
            fields='parents'
        ).execute()
        
        previous_parents = ",".join(file.get('parents'))
        
        self.drive_service.files().update(
            fileId=spreadsheet_id,
            addParents=self.main_folder_id,
            removeParents=previous_parents,
            fields='id, parents'
        ).execute()
        
        # Add headers
        values = [
            ['Participant Name', 'Company', 'Status', 'Date Submitted', 'Date Approved', 'Feedback Notes', 'Last Updated']
        ]
        
        body = {
            'values': values
        }
        
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='Approval Status!A1',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        # Format headers
        requests = [{
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {
                            'red': 0.83,
                            'green': 0.83,
                            'blue': 0.83
                        },
                        'textFormat': {
                            'bold': True
                        },
                        'horizontalAlignment': 'CENTER'
                    }
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)'
            }
        }]
        
        # Add data validation for Status column
        requests.append({
            'setDataValidation': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 1,
                    'endRowIndex': 1000,
                    'startColumnIndex': 2,
                    'endColumnIndex': 3
                },
                'rule': {
                    'condition': {
                        'type': 'ONE_OF_LIST',
                        'values': [
                            {'userEnteredValue': 'Pending'},
                            {'userEnteredValue': 'Approved'},
                            {'userEnteredValue': 'Needs Edits'}
                        ]
                    },
                    'showCustomUi': True,
                    'strict': True
                }
            }
        })
        
        # Add conditional formatting
        # For Approved
        requests.append({
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{
                        'sheetId': 0,
                        'startRowIndex': 1,
                        'endRowIndex': 1000,
                        'startColumnIndex': 2,
                        'endColumnIndex': 3
                    }],
                    'booleanRule': {
                        'condition': {
                            'type': 'TEXT_EQ',
                            'values': [{'userEnteredValue': 'Approved'}]
                        },
                        'format': {
                            'backgroundColor': {
                                'red': 0.7,
                                'green': 0.9,
                                'blue': 0.7
                            }
                        }
                    }
                },
                'index': 0
            }
        })
        
        # For Pending
        requests.append({
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{
                        'sheetId': 0,
                        'startRowIndex': 1,
                        'endRowIndex': 1000,
                        'startColumnIndex': 2,
                        'endColumnIndex': 3
                    }],
                    'booleanRule': {
                        'condition': {
                            'type': 'TEXT_EQ',
                            'values': [{'userEnteredValue': 'Pending'}]
                        },
                        'format': {
                            'backgroundColor': {
                                'red': 1.0,
                                'green': 1.0,
                                'blue': 0.7
                            }
                        }
                    }
                },
                'index': 1
            }
        })
        
        # For Needs Edits
        requests.append({
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{
                        'sheetId': 0,
                        'startRowIndex': 1,
                        'endRowIndex': 1000,
                        'startColumnIndex': 2,
                        'endColumnIndex': 3
                    }],
                    'booleanRule': {
                        'condition': {
                            'type': 'TEXT_EQ',
                            'values': [{'userEnteredValue': 'Needs Edits'}]
                        },
                        'format': {
                            'backgroundColor': {
                                'red': 1.0,
                                'green': 0.8,
                                'blue': 0.8
                            }
                        }
                    }
                },
                'index': 2
            }
        })
        
        self.sheets_service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={'requests': requests}
        ).execute()
        
        print(f"Created approval tracker: {spreadsheet_title}")
        return spreadsheet_id
    
    def add_participants_to_sheet(self, spreadsheet_id, participants_data):
        """Add participant data to the Google Sheet."""
        # Prepare data for insertion
        values = []
        for participant in participants_data:
            values.append([
                participant.get('name', ''),
                participant.get('role', ''),
                participant.get('country', ''),
                participant.get('company', ''),
                participant.get('linkedin_url', ''),
                participant.get('notes', '')
            ])
        
        if not values:
            print("No participant data to add")
            return
        
        body = {
            'values': values
        }
        
        # Append data to the sheet
        result = self.sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Participants!A2',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        print(f"Added {len(values)} participants to sheet")
        return result
    
    def add_participant_to_approval_tracker(self, spreadsheet_id, participant_name, company_name):
        """Add a participant to the approval tracker."""
        # Current date for submission
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        values = [[
            participant_name,
            company_name,
            'Pending',  # Initial status
            current_date,  # Date submitted
            '',  # Date approved (empty initially)
            '',  # Feedback notes
            current_date  # Last updated
        ]]
        
        body = {
            'values': values
        }
        
        # Append data to the sheet
        result = self.sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='Approval Status!A2',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()
        
        print(f"Added {participant_name} to approval tracker")
        return result
    
    def upload_docx_to_drive(self, file_path, folder_id, file_name=None):
        """Upload a DOCX file to Google Drive."""
        if not file_name:
            file_name = os.path.basename(file_path)
            
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(
            file_path,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            resumable=True
        )
        
        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"Uploaded file: {file_name}, ID: {file.get('id')}")
        return file.get('id')
    
    def upload_pdf_to_drive(self, file_path, folder_id, file_name=None):
        """Upload a PDF file to Google Drive."""
        if not file_name:
            file_name = os.path.basename(file_path)
            
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(
            file_path,
            mimetype='application/pdf',
            resumable=True
        )
        
        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"Uploaded file: {file_name}, ID: {file.get('id')}")
        return file.get('id')
    
    def upload_image_to_drive(self, file_path, folder_id, file_name=None):
        """Upload an image file to Google Drive."""
        if not file_name:
            file_name = os.path.basename(file_path)
        
        # Determine MIME type based on file extension
        mime_type = 'image/png'  # Default to PNG
        if file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
            mime_type = 'image/jpeg'
            
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )
        
        file = self.drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"Uploaded image: {file_name}, ID: {file.get('id')}")
        return file.get('id')
    
    def update_approval_status(self, spreadsheet_id, participant_name, status, feedback=None):
        """Update the approval status for a participant."""
        # Get all data from the sheet to find the row for this participant
        result = self.sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Approval Status!A:G'
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            print("No data found in approval tracker")
            return False
        
        # Find the row with this participant name
        row_index = None
        for i, row in enumerate(values):
            if i > 0 and len(row) > 0 and row[0] == participant_name:
                row_index = i + 1  # +1 because sheets are 1-indexed
                break
        
        if not row_index:
            print(f"Participant {participant_name} not found in approval tracker")
            return False
        
        # Prepare the update data
        current_date = datetime.now().strftime('%Y-%m-%d')
        update_data = []
        
        # Status update (column C)
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f'Approval Status!C{row_index}',
            valueInputOption='RAW',
            body={
                'values': [[status]]
            }
        ).execute()
        
        # Date approved update if approved (column E)
        if status == 'Approved':
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'Approval Status!E{row_index}',
                valueInputOption='RAW',
                body={
                    'values': [[current_date]]
                }
            ).execute()
        
        # Feedback notes update if provided (column F)
        if feedback:
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f'Approval Status!F{row_index}',
                valueInputOption='RAW',
                body={
                    'values': [[feedback]]
                }
            ).execute()
        
        # Last updated (column G)
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f'Approval Status!G{row_index}',
            valueInputOption='RAW',
            body={
                'values': [[current_date]]
            }
        ).execute()
        
        print(f"Updated approval status for {participant_name} to {status}")
        return True


# Initialize the service
def get_drive_service():
    """Get an instance of the Google Drive service."""
    return GoogleDriveService()
