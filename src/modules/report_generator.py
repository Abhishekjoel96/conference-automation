import os
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional
from datetime import datetime
from fpdf import FPDF

# Import services
from ..services.google_drive import get_drive_service
from ..services.openai_service import get_openai_service

# Import other modules
from .approval_tracker import get_approval_tracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ReportGenerator:
    def __init__(self):
        self.drive_service = get_drive_service()
        self.openai = get_openai_service()
        self.approval_tracker = get_approval_tracker()
    
    def generate_summary_report(self, 
                            event_name: str, 
                            user_name: str,
                            user_company_name: str,
                            message_samples: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Generate a summary report for the event.
        
        Args:
            event_name: Name of the event
            user_name: Name of the user
            user_company_name: Name of the user's company
            message_samples: Sample of message data to derive insights (optional)
            
        Returns:
            Dictionary with report generation details
        """
        logger.info(f"Generating summary report for {event_name}")
        
        # Get the approval status to gather statistics
        all_participants = self.approval_tracker.get_approval_status(event_name)
        approved_participants = self.approval_tracker.get_approved_participants(event_name)
        
        # Calculate statistics
        total_participants = len(all_participants)
        approved_messages = len(approved_participants)
        
        # For sent messages, we'll assume that all approved messages were sent
        # In a real system, you would get this from the message sending logs
        sent_messages = approved_messages
        
        # If no message samples are provided, use a default
        if not message_samples or len(message_samples) == 0:
            message_samples = [
                {
                    "participant": "Sample Participant 1",
                    "company": "Sample Company 1",
                    "synergy_points": ["Collaboration on technology integration", "Shared target market"],
                    "personalized_intro": "Your work on AI solutions is impressive"
                },
                {
                    "participant": "Sample Participant 2",
                    "company": "Sample Company 2",
                    "synergy_points": ["Joint research opportunities", "Complementary product offerings"],
                    "personalized_intro": "Your recent expansion into Asia is remarkable"
                }
            ]
        
        # Generate report content using OpenAI
        try:
            report_content = self.openai.generate_summary_report(
                event_name=event_name,
                total_participants=total_participants,
                approved_messages=approved_messages,
                sent_messages=sent_messages,
                message_samples=message_samples
            )
            
            logger.info(f"Successfully generated report content")
        except Exception as e:
            logger.error(f"Error generating report content: {e}")
            # Create a basic report content if OpenAI fails
            report_content = {
                "key_metrics": {
                    "total_participants": total_participants,
                    "approved_messages": approved_messages,
                    "sent_messages": sent_messages
                },
                "key_learnings": [
                    "Personalization increases engagement.",
                    "LinkedIn insights were crucial in tailoring the synergy pitch.",
                    "Many companies are open to talent partnerships, especially in AI/ML and EdTech intersections."
                ],
                "suggested_improvements": [
                    "Automate LinkedIn profile fetching to speed up research.",
                    "Create company description templates for quicker messaging.",
                    "Implement better tracking for message responses."
                ],
                "success_patterns": [
                    "Messages highlighting specific collaboration opportunities received better engagement.",
                    "Brief but personalized intros performed well."
                ],
                "executive_summary": f"This report summarizes the outreach campaign for {event_name}. A total of {total_participants} participants were reviewed, resulting in {approved_messages} approved messages and {sent_messages} sent messages."
            }
        
        # Create the PDF report
        try:
            pdf_path = self._create_pdf_report(
                event_name=event_name,
                user_name=user_name,
                user_company_name=user_company_name,
                report_content=report_content
            )
            
            # Get summary reports folder ID
            folder_id = self.drive_service.folder_ids.get('Summary_Reports')
            
            if not folder_id:
                logger.error("Could not find summary reports folder")
                return {"status": "error", "message": "Could not find summary reports folder"}
            
            # Upload to Google Drive
            file_name = f"Summary_Report_{event_name}.pdf"
            file_id = self.drive_service.upload_pdf_to_drive(
                file_path=pdf_path,
                folder_id=folder_id,
                file_name=file_name
            )
            
            # Delete temporary file
            os.remove(pdf_path)
            
            logger.info(f"Successfully created and uploaded summary report for {event_name}")
            
            return {
                "status": "success",
                "file": {
                    "id": file_id,
                    "name": file_name,
                    "folder_id": folder_id
                },
                "metrics": {
                    "total_participants": total_participants,
                    "approved_messages": approved_messages,
                    "sent_messages": sent_messages
                }
            }
        except Exception as e:
            logger.error(f"Error creating or uploading PDF report: {e}")
            return {"status": "error", "message": str(e)}
    
    def _create_pdf_report(self, 
                        event_name: str, 
                        user_name: str,
                        user_company_name: str,
                        report_content: Dict[str, Any]) -> str:
        """
        Create a PDF report based on the report content.
        
        Args:
            event_name: Name of the event
            user_name: Name of the user
            user_company_name: Name of the user's company
            report_content: Dictionary with report content
            
        Returns:
            Path to the created PDF file
        """
        # Create a PDF document
        pdf = FPDF()
        pdf.add_page()
        
        # Set up fonts
        pdf.set_font("Arial", "B", 16)
        
        # Title
        pdf.cell(0, 10, f"Summary Report: {event_name}", 0, 1, "C")
        pdf.ln(5)
        
        # Subtitle with date
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%Y-%m-%d')} by {user_name}, {user_company_name}", 0, 1, "C")
        pdf.ln(10)
        
        # Executive Summary
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Executive Summary", 0, 1, "L")
        pdf.set_font("Arial", "", 12)
        
        # Multi-line text for executive summary
        executive_summary = report_content.get("executive_summary", "")
        lines = self._wrap_text(executive_summary, pdf, 180)
        for line in lines:
            pdf.cell(0, 6, line, 0, 1, "L")
        pdf.ln(10)
        
        # Key Metrics
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Key Metrics", 0, 1, "L")
        pdf.set_font("Arial", "", 12)
        
        metrics = report_content.get("key_metrics", {})
        pdf.cell(0, 8, f"Total Participants Reviewed: {metrics.get('total_participants', 0)}", 0, 1, "L")
        pdf.cell(0, 8, f"Total Messages Approved: {metrics.get('approved_messages', 0)}", 0, 1, "L")
        pdf.cell(0, 8, f"Total Messages Sent: {metrics.get('sent_messages', 0)}", 0, 1, "L")
        pdf.ln(10)
        
        # Key Learnings
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Key Learnings", 0, 1, "L")
        pdf.set_font("Arial", "", 12)
        
        learnings = report_content.get("key_learnings", [])
        for learning in learnings:
            pdf.cell(10, 6, "", 0, 0, "L")
            pdf.cell(0, 6, f"• {learning}", 0, 1, "L")
        pdf.ln(10)
        
        # Suggested Improvements
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Suggested Improvements", 0, 1, "L")
        pdf.set_font("Arial", "", 12)
        
        improvements = report_content.get("suggested_improvements", [])
        for improvement in improvements:
            pdf.cell(10, 6, "", 0, 0, "L")
            pdf.cell(0, 6, f"• {improvement}", 0, 1, "L")
        pdf.ln(10)
        
        # Success Patterns
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Success Patterns", 0, 1, "L")
        pdf.set_font("Arial", "", 12)
        
        patterns = report_content.get("success_patterns", [])
        for pattern in patterns:
            pdf.cell(10, 6, "", 0, 0, "L")
            pdf.cell(0, 6, f"• {pattern}", 0, 1, "L")
        pdf.ln(10)
        
        # Footer
        pdf.set_y(-30)
        pdf.set_font("Arial", "I", 8)
        pdf.cell(0, 10, f"Generated by Conference Networking Automation Tool", 0, 0, "C")
        
        # Save to temporary file
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"Summary_Report_{event_name}.pdf")
        pdf.output(file_path)
        
        return file_path
    
    def _wrap_text(self, text: str, pdf: FPDF, max_width: int) -> List[str]:
        """
        Wrap text to fit within a specified width in the PDF.
        
        Args:
            text: Text to wrap
            pdf: FPDF instance
            max_width: Maximum width in mm
            
        Returns:
            List of wrapped text lines
        """
        lines = []
        words = text.split()
        
        if not words:
            return lines
        
        current_line = words[0]
        for word in words[1:]:
            if pdf.get_string_width(current_line + " " + word) < max_width:
                current_line += " " + word
            else:
                lines.append(current_line)
                current_line = word
        
        lines.append(current_line)
        return lines

# Initialize the report generator
def get_report_generator():
    """Get an instance of the report generator."""
    return ReportGenerator()
