#!/usr/bin/env python3

import os
import sys
import json
import argparse
import logging
from typing import Dict, List, Any, Optional

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import modules
from src.modules.participant_scraper import get_participant_scraper
from src.modules.linkedin_research import get_linkedin_researcher
from src.modules.message_generator import get_message_generator
from src.modules.approval_tracker import get_approval_tracker
from src.modules.message_sender import get_message_sender
from src.modules.report_generator import get_report_generator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def scrape_participants(args):
    """Scrape participants from a conference website."""
    scraper = get_participant_scraper()
    
    # Check for required args
    if not args.event_name:
        logger.error("Event name is required")
        return
    
    if not args.conference_url:
        logger.error("Conference URL is required")
        return
    
    # No phantom ID needed for ProxyCurl conference scraping
    # Note: ProxyCurl doesn't directly support conference website scraping
    
    # Scrape participants
    result = scraper.scrape_participants(
        event_name=args.event_name,
        conference_url=args.conference_url
    )
    
    if result:
        logger.info(f"Successfully scraped {len(result)} participants")
    else:
        logger.error("Failed to scrape participants")


def manual_input_participants(args):
    """Manually input participants when scraping fails."""
    scraper = get_participant_scraper()
    
    # Check for required args
    if not args.event_name:
        logger.error("Event name is required")
        return
    
    if not args.input_file:
        logger.error("Input file is required for manual input")
        return
    
    # Load participants from input file
    try:
        with open(args.input_file, 'r') as f:
            participants_data = json.load(f)
        
        # Process participants
        result = scraper.fallback_manual_input(
            event_name=args.event_name,
            participants_data=participants_data
        )
        
        if result:
            logger.info(f"Successfully processed {len(result)} participants")
        else:
            logger.error("Failed to process participants")
    except Exception as e:
        logger.error(f"Error processing input file: {e}")


def generate_messages(args):
    """Generate personalized messages for participants."""
    generator = get_message_generator()
    
    # Check for required args
    if not args.event_name:
        logger.error("Event name is required")
        return
    
    if not args.user_name:
        logger.error("User name is required")
        return
    
    if not args.user_role:
        logger.error("User role is required")
        return
    
    if not args.company_name:
        logger.error("Company name is required")
        return
    
    if not args.company_description:
        logger.error("Company description is required")
        return
    
    # Load participants if input file is provided
    if args.input_file:
        try:
            with open(args.input_file, 'r') as f:
                participants_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading participants from file: {e}")
            return
    else:
        # If no input file, check if we should generate for all participants
        if args.all_participants:
            # TODO: Implement fetching all participants from Google Sheets
            logger.error("Fetching all participants from Google Sheets not implemented yet")
            return
        else:
            logger.error("Either --input-file or --all-participants is required")
            return
    
    # Process participants and generate messages
    result = generator.process_participants_batch(
        event_name=args.event_name,
        participants_data=participants_data,
        user_name=args.user_name,
        user_role=args.user_role,
        user_company_name=args.company_name,
        user_company_description=args.company_description,
        # No phantom ID needed for ProxyCurl
    )
    
    logger.info(f"Message generation complete. Successful: {result['successful']}, Failed: {result['failed']}")


def update_approval(args):
    """Update approval status for a participant."""
    tracker = get_approval_tracker()
    
    # Check for required args
    if not args.event_name:
        logger.error("Event name is required")
        return
    
    if not args.participant_name:
        logger.error("Participant name is required")
        return
    
    if not args.status:
        logger.error("Status is required")
        return
    
    # Validate status
    valid_statuses = ["Approved", "Needs Edits", "Pending"]
    if args.status not in valid_statuses:
        logger.error(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        return
    
    # Update status
    result = tracker.update_participant_status(
        event_name=args.event_name,
        participant_name=args.participant_name,
        status=args.status,
        feedback=args.feedback
    )
    
    if result:
        logger.info(f"Successfully updated status for {args.participant_name} to {args.status}")
    else:
        logger.error(f"Failed to update status for {args.participant_name}")


def list_approval_status(args):
    """List approval status for all participants."""
    tracker = get_approval_tracker()
    
    # Check for required args
    if not args.event_name:
        logger.error("Event name is required")
        return
    
    # Get approval status
    status = tracker.get_approval_status(args.event_name)
    
    if status:
        print(f"\nApproval Status for {args.event_name}:\n")
        print(f"{'Participant Name':<30} {'Company':<30} {'Status':<15} {'Date Submitted':<15} {'Date Approved':<15}")
        print("-" * 105)
        
        for participant in status:
            name = participant.get('Participant Name', '')
            company = participant.get('Company', '')
            status_val = participant.get('Status', '')
            date_submitted = participant.get('Date Submitted', '')
            date_approved = participant.get('Date Approved', '')
            
            print(f"{name:<30} {company:<30} {status_val:<15} {date_submitted:<15} {date_approved:<15}")
        
        print(f"\nTotal participants: {len(status)}\n")
    else:
        logger.info(f"No participants found for {args.event_name}")


def send_messages(args):
    """Simulate sending messages to approved participants."""
    sender = get_message_sender()
    
    # Check for required args
    if not args.event_name:
        logger.error("Event name is required")
        return
    
    # Process approved messages
    result = sender.process_approved_messages(
        event_name=args.event_name,
        conference_platform_url=args.platform_url
    )
    
    if result['status'] == 'completed':
        logger.info(f"Message sending simulation complete. Successful: {result['successful']}, Failed: {result['failed']}")
    else:
        logger.error("Failed to process approved messages")


def generate_report(args):
    """Generate a summary report for the event."""
    reporter = get_report_generator()
    
    # Check for required args
    if not args.event_name:
        logger.error("Event name is required")
        return
    
    if not args.user_name:
        logger.error("User name is required")
        return
    
    if not args.company_name:
        logger.error("Company name is required")
        return
    
    # Generate report
    result = reporter.generate_summary_report(
        event_name=args.event_name,
        user_name=args.user_name,
        user_company_name=args.company_name
    )
    
    if result['status'] == 'success':
        logger.info(f"Summary report generated successfully")
        logger.info(f"Report file: {result['file']['name']}")
        logger.info(f"Total participants: {result['metrics']['total_participants']}")
        logger.info(f"Approved messages: {result['metrics']['approved_messages']}")
        logger.info(f"Sent messages: {result['metrics']['sent_messages']}")
    else:
        logger.error(f"Failed to generate report: {result.get('message', 'Unknown error')}")


def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(description="Conference Networking Automation Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Scrape participants command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape participants from a conference website")
    scrape_parser.add_argument("--event-name", required=True, help="Name of the event")
    scrape_parser.add_argument("--conference-url", required=True, help="URL of the conference website")
    # No phantom ID needed for ProxyCurl
    
    # Manual input command
    manual_parser = subparsers.add_parser("manual-input", help="Manually input participants when scraping fails")
    manual_parser.add_argument("--event-name", required=True, help="Name of the event")
    manual_parser.add_argument("--input-file", required=True, help="JSON file with participant data")
    
    # Generate messages command
    generate_parser = subparsers.add_parser("generate-messages", help="Generate personalized messages for participants")
    generate_parser.add_argument("--event-name", required=True, help="Name of the event")
    generate_parser.add_argument("--user-name", required=True, help="Name of the user")
    generate_parser.add_argument("--user-role", required=True, help="Role of the user")
    generate_parser.add_argument("--company-name", required=True, help="Name of the user's company")
    generate_parser.add_argument("--company-description", required=True, help="Description of the user's company")
    generate_parser.add_argument("--input-file", help="JSON file with participant data")
    generate_parser.add_argument("--all-participants", action="store_true", help="Generate messages for all participants")
    # No phantom ID needed for ProxyCurl
    
    # Update approval command
    approval_parser = subparsers.add_parser("update-approval", help="Update approval status for a participant")
    approval_parser.add_argument("--event-name", required=True, help="Name of the event")
    approval_parser.add_argument("--participant-name", required=True, help="Name of the participant")
    approval_parser.add_argument("--status", required=True, choices=["Approved", "Needs Edits", "Pending"], help="Approval status")
    approval_parser.add_argument("--feedback", help="Feedback for the participant")
    
    # List approval status command
    list_parser = subparsers.add_parser("list-approval", help="List approval status for all participants")
    list_parser.add_argument("--event-name", required=True, help="Name of the event")
    
    # Send messages command
    send_parser = subparsers.add_parser("send-messages", help="Simulate sending messages to approved participants")
    send_parser.add_argument("--event-name", required=True, help="Name of the event")
    send_parser.add_argument("--platform-url", help="URL of the conference platform")
    
    # Generate report command
    report_parser = subparsers.add_parser("generate-report", help="Generate a summary report for the event")
    report_parser.add_argument("--event-name", required=True, help="Name of the event")
    report_parser.add_argument("--user-name", required=True, help="Name of the user")
    report_parser.add_argument("--company-name", required=True, help="Name of the user's company")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == "scrape":
        scrape_participants(args)
    elif args.command == "manual-input":
        manual_input_participants(args)
    elif args.command == "generate-messages":
        generate_messages(args)
    elif args.command == "update-approval":
        update_approval(args)
    elif args.command == "list-approval":
        list_approval_status(args)
    elif args.command == "send-messages":
        send_messages(args)
    elif args.command == "generate-report":
        generate_report(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
