import os
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional
from datetime import datetime
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Import services
from ..services.google_drive import get_drive_service
from googleapiclient.http import MediaFileUpload

# Import other modules
from .approval_tracker import get_approval_tracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MessageSender:
    def __init__(self):
        self.drive_service = get_drive_service()
        self.approval_tracker = get_approval_tracker()
    
    def simulate_sending_message(self, 
                             event_name: str, 
                             participant_name: str,
                             message_text: str,
                             conference_platform_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Simulate sending a message to a participant and take screenshots.
        
        Args:
            event_name: Name of the event
            participant_name: Name of the participant
            message_text: Text of the message to send
            conference_platform_url: URL of the conference platform (optional)
            
        Returns:
            Dictionary with sending simulation details
        """
        logger.info(f"Simulating sending message to {participant_name}")
        
        # Get event folders
        event_folders = self.drive_service.create_event_folders(event_name)
        log_folder_id = event_folders.get(f"Sent_Messages_Log_{event_name}")
        
        if not log_folder_id:
            logger.error(f"Could not find sent messages log folder for {event_name}")
            return {"status": "error", "message": "Could not find log folder"}
        
        # Prepare result dictionary
        result = {
            "participant": participant_name,
            "status": "simulated",
            "timestamp": datetime.now().isoformat(),
            "screenshots": [],
            "log_entry": {}
        }
        
        # Check if conference platform URL is provided
        if conference_platform_url:
            # Take screenshots of the message being composed
            try:
                screenshot_paths = self._take_platform_screenshots(
                    conference_platform_url=conference_platform_url,
                    participant_name=participant_name,
                    message_text=message_text
                )
                
                # Upload screenshots to Google Drive
                for i, screenshot_path in enumerate(screenshot_paths):
                    file_name = f"{participant_name} - Screenshot_{i+1}.png"
                    file_id = self.drive_service.upload_image_to_drive(
                        file_path=screenshot_path,
                        folder_id=log_folder_id,
                        file_name=file_name
                    )
                    
                    result["screenshots"].append({
                        "id": file_id,
                        "name": file_name,
                        "folder_id": log_folder_id
                    })
                    
                    # Delete temporary file
                    os.remove(screenshot_path)
                
                logger.info(f"Successfully took {len(screenshot_paths)} screenshots for {participant_name}")
            except Exception as e:
                logger.error(f"Error taking screenshots: {e}")
                # Continue with the simulation even if screenshots fail
        
        # Create a log entry document
        log_entry = {
            "participant": participant_name,
            "event": event_name,
            "message": message_text,
            "timestamp": datetime.now().isoformat(),
            "platform": conference_platform_url if conference_platform_url else "Not specified",
            "status": "Simulated sending"
        }
        
        # Save log entry as JSON
        try:
            temp_dir = tempfile.gettempdir()
            log_file_path = os.path.join(temp_dir, f"{participant_name} - Send Log.json")
            
            with open(log_file_path, 'w') as f:
                json.dump(log_entry, f, indent=2)
            
            # Upload to Google Drive
            file_name = f"{participant_name} - Send Log.json"
            file_id = self.drive_service.drive_service.files().create(
                body={
                    'name': file_name,
                    'parents': [log_folder_id],
                    'mimeType': 'application/json'
                },
                media_body=MediaFileUpload(
                    log_file_path,
                    mimetype='application/json',
                    resumable=True
                ),
                fields='id'
            ).execute().get('id')
            
            result["log_entry"] = {
                "id": file_id,
                "name": file_name,
                "folder_id": log_folder_id
            }
            
            # Delete temporary file
            os.remove(log_file_path)
            
            logger.info(f"Successfully saved log entry for {participant_name}")
        except Exception as e:
            logger.error(f"Error creating log entry: {e}")
            result["log_entry"] = {"error": str(e)}
        
        return result
    
    def _take_platform_screenshots(self, 
                                conference_platform_url: str, 
                                participant_name: str, 
                                message_text: str) -> List[str]:
        """
        Take screenshots of the message being composed on the conference platform.
        
        Args:
            conference_platform_url: URL of the conference platform
            participant_name: Name of the participant
            message_text: Text of the message to send
            
        Returns:
            List of paths to the screenshot files
        """
        logger.info(f"Taking screenshots for {participant_name} on {conference_platform_url}")
        
        screenshot_paths = []
        
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Initialize WebDriver
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            
            # Navigate to the conference platform
            driver.get(conference_platform_url)
            driver.implicitly_wait(10)
            
            # Take a screenshot of the initial page
            temp_dir = tempfile.gettempdir()
            initial_screenshot_path = os.path.join(temp_dir, f"{participant_name}_screenshot_1.png")
            driver.save_screenshot(initial_screenshot_path)
            screenshot_paths.append(initial_screenshot_path)
            
            # Since this is a simulation, we'll just create a mockup of the message composition
            # This would need to be adapted for the specific conference platform
            
            # Create a simple HTML message composition mockup
            mockup_html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .message-box {{ border: 1px solid #ccc; padding: 10px; width: 80%; margin: 20px auto; }}
                    .header {{ background-color: #f0f0f0; padding: 10px; }}
                    .content {{ padding: 15px; }}
                    .footer {{ padding: 10px; text-align: right; }}
                    .button {{ background-color: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; }}
                </style>
            </head>
            <body>
                <h2>Conference Messaging Platform - Simulation</h2>
                <div class="message-box">
                    <div class="header">
                        <strong>To:</strong> {participant_name}
                    </div>
                    <div class="content">
                        <textarea style="width: 100%; height: 200px;">{message_text}</textarea>
                    </div>
                    <div class="footer">
                        <button class="button">Send Message</button>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Navigate to the mockup
            driver.execute_script(f"document.body.innerHTML = `{mockup_html}`;")
            
            # Take a screenshot of the message composition
            composition_screenshot_path = os.path.join(temp_dir, f"{participant_name}_screenshot_2.png")
            driver.save_screenshot(composition_screenshot_path)
            screenshot_paths.append(composition_screenshot_path)
            
            # Simulate clicking the send button
            driver.execute_script("document.querySelector('.button').style.backgroundColor = '#2E8B57';")
            driver.execute_script("document.querySelector('.button').textContent = 'Message Sent';")
            
            # Take a screenshot of the "sent" state
            sent_screenshot_path = os.path.join(temp_dir, f"{participant_name}_screenshot_3.png")
            driver.save_screenshot(sent_screenshot_path)
            screenshot_paths.append(sent_screenshot_path)
            
            # Clean up
            driver.quit()
            
            logger.info(f"Successfully took {len(screenshot_paths)} screenshots")
            return screenshot_paths
            
        except Exception as e:
            logger.error(f"Error taking screenshots: {e}")
            # If we have partial screenshots, return those
            if screenshot_paths:
                return screenshot_paths
            
            # Create a fallback screenshot with error message
            temp_dir = tempfile.gettempdir()
            fallback_path = os.path.join(temp_dir, f"{participant_name}_fallback.png")
            
            # Create a simple error image
            try:
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new('RGB', (800, 400), color=(255, 255, 255))
                d = ImageDraw.Draw(img)
                d.text((10, 10), f"Error taking screenshot: {e}", fill=(0, 0, 0))
                d.text((10, 50), f"Participant: {participant_name}", fill=(0, 0, 0))
                d.text((10, 90), f"Platform: {conference_platform_url}", fill=(0, 0, 0))
                d.text((10, 130), "This is a fallback screenshot for simulation purposes.", fill=(0, 0, 0))
                img.save(fallback_path)
                return [fallback_path]
            except Exception:
                # If even the fallback fails, return an empty list
                return []
    
    def process_approved_messages(self, 
                               event_name: str, 
                               conference_platform_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Process all approved messages for sending simulation.
        
        Args:
            event_name: Name of the event
            conference_platform_url: URL of the conference platform (optional)
            
        Returns:
            Dictionary with processing statistics
        """
        logger.info(f"Processing approved messages for {event_name}")
        
        # Get approved participants
        approved_participants = self.approval_tracker.get_approved_participants(event_name)
        
        if not approved_participants:
            logger.warning(f"No approved participants found for {event_name}")
            return {
                "status": "completed",
                "total": 0,
                "successful": 0,
                "failed": 0,
                "participants": []
            }
        
        results = {
            "status": "completed",
            "total": len(approved_participants),
            "successful": 0,
            "failed": 0,
            "participants": []
        }
        
        # Process each approved participant
        for participant in approved_participants:
            try:
                # Get the participant's message
                participant_name = participant.get('Participant Name')
                
                # Simulate fetching the approved message (in a real system, you would get this from Drive)
                # For this simulation, we'll create a simple message
                message_text = f"Dear {participant_name}, This is a simulated message for the {event_name} conference..."
                
                # Simulate sending the message
                send_result = self.simulate_sending_message(
                    event_name=event_name,
                    participant_name=participant_name,
                    message_text=message_text,
                    conference_platform_url=conference_platform_url
                )
                
                if send_result.get('status') == 'simulated':
                    results["successful"] += 1
                    results["participants"].append({
                        "name": participant_name,
                        "status": "success",
                        "screenshots": send_result.get('screenshots', []),
                        "log_entry": send_result.get('log_entry', {})
                    })
                else:
                    results["failed"] += 1
                    results["participants"].append({
                        "name": participant_name,
                        "status": "failed",
                        "error": send_result.get('message', 'Unknown error')
                    })
            except Exception as e:
                logger.error(f"Error processing approved participant {participant.get('Participant Name')}: {e}")
                results["failed"] += 1
                results["participants"].append({
                    "name": participant.get('Participant Name'),
                    "status": "failed",
                    "error": str(e)
                })
        
        logger.info(f"Completed processing {results['total']} approved messages. Successful: {results['successful']}, Failed: {results['failed']}")
        return results

# Initialize the message sender
def get_message_sender():
    """Get an instance of the message sender."""
    return MessageSender()
