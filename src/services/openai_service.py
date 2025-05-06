import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from ..config import OPENAI_API_KEY, COMPANY_DESCRIPTION_TEMPLATE, MESSAGE_TEMPLATE

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = "gpt-4-turbo"  # Can be configured based on needs
    
    def generate_research_summary(self, 
                               person_info: Dict[str, Any], 
                               company_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a research summary based on the information collected about a person and their company.
        
        Args:
            person_info: Dictionary with information about the person
            company_info: Dictionary with information about the company
            
        Returns:
            Dictionary with research summary sections
        """
        prompt = f"""
        Based on the following information, create a concise research summary about a professional and their company.
        Format your response as JSON with the following sections:
        1. person_summary - Key facts about the person (role, background, achievements)
        2. company_summary - Key information about the company (what they do, market, funding, impact)
        3. notable_points - Any notable or interesting points about the person or company
        
        PERSON INFORMATION:
        {json.dumps(person_info, indent=2)}
        
        COMPANY INFORMATION:
        {json.dumps(company_info, indent=2)}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a professional business researcher who provides concise, accurate information."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error generating research summary: {e}")
            # Return a basic structure in case of error
            return {
                "person_summary": f"Summary for {person_info['name']} could not be generated.",
                "company_summary": f"Summary for {company_info['name']} could not be generated.",
                "notable_points": ["Error generating research."]
            }
    
    def identify_synergies(self, 
                         research_summary: Dict[str, Any], 
                         user_company_description: str) -> List[str]:
        """
        Identify potential areas of synergy between the user's company and the participant's company.
        
        Args:
            research_summary: Research summary dictionary
            user_company_description: Description of the user's company
            
        Returns:
            List of potential synergy points
        """
        prompt = f"""
        Identify 2-3 specific areas of potential collaboration or synergy between these two companies:
        
        PARTICIPANT/COMPANY RESEARCH:
        {json.dumps(research_summary, indent=2)}
        
        USER'S COMPANY:
        {user_company_description}
        
        Format your response as a JSON array of strings, with each string being a specific synergy point.
        Each point should be 1-2 sentences long, specific, and highlight mutual benefit.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are a strategic business development expert who identifies mutually beneficial partnership opportunities."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            return result.get("synergies", [])
            
        except Exception as e:
            print(f"Error identifying synergies: {e}")
            return ["Could not identify specific synergies due to an error."]
    
    def generate_personalized_message(self, 
                                   participant_name: str,
                                   participant_role: str,
                                   participant_company: str,
                                   research_summary: Dict[str, Any],
                                   synergy_points: List[str],
                                   user_name: str,
                                   user_role: str,
                                   user_company_name: str,
                                   user_company_description: str,
                                   synergy_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a personalized outreach message based on research and identified synergies.
        
        Args:
            participant_name: Name of the participant
            participant_role: Role/position of the participant
            participant_company: Company name of the participant
            research_summary: Research summary dictionary
            synergy_points: List of identified synergy points
            user_name: Name of the user
            user_role: Role/position of the user
            user_company_name: Name of the user's company
            user_company_description: Description of the user's company
            synergy_info: Optional additional structured synergy information from SerpAPI
            
        Returns:
            Dictionary with research summary, synergy points, and message draft
        """
        # Add synergy info to the prompt if available
        synergy_info_text = ""
        if synergy_info:
            synergy_info_text = f"""
            
            DETAILED SYNERGY ANALYSIS:
            {json.dumps(synergy_info, indent=2)}
            """
        
        prompt = f"""
        Create a highly personalized networking message from {user_name} ({user_role} at {user_company_name}) 
        to {participant_name} ({participant_role} at {participant_company}) based on deep research analysis.
        
        Use this research and synergy information:
        
        RESEARCH SUMMARY:
        {json.dumps(research_summary, indent=2)}
        
        SYNERGY POINTS:
        {json.dumps(synergy_points, indent=2)}{synergy_info_text}
        
        USER'S COMPANY DESCRIPTION:
        {user_company_description}
        
        Format your response as JSON with the following exact format:
        {{
            "research_summary": {{
                "name": "{participant_name}",
                "role": "{participant_role} at {participant_company}",
                "company": "Detailed company description focusing on their primary products/services, market position, and unique value proposition",
                "linkedin": "LinkedIn Profile URL or note",
                "background": "Comprehensive background information including career trajectory, notable achievements, and expertise areas",
                "areas_of_synergy": ["4-5 specific, actionable collaboration opportunities based on both companies' strengths and market positions"]
            }},
            "message_draft": "Complete personalized message with the following structure:\n\nHi [First Name],\n\nPersonal introduction that mentions the conference and establishes credibility through your role at {user_company_name}. Include 1-2 sentences about your company that are directly relevant to the recipient's interests.\n\nSpecific, detailed reference to their recent work, achievements, or company initiatives that genuinely impressed you. Be specific and show you've done your research.\n\n1-2 paragraphs outlining concrete collaboration opportunities with specific benefits for both parties. Reference how your expertise/product/service addresses their specific challenges.\n\nClear, direct request for a meeting at the conference with specific time options or a virtual follow-up meeting.\n\nWarm, enthusiastic closing that expresses genuine interest in their response.\n\nBest regards,\n{user_name}\n{user_role}, {user_company_name}"
        }}
        
        IMPORTANT GUIDELINES:
        1. The research summary must be detailed, accurate, and tailored specifically to this individual and their company.
        2. The message must be warm, professional (150-250 words), and emphasize mutual benefit rather than just selling.
        3. Include specific details from their background or company that shows you've done thorough research.
        4. Mention the conference by name and reference it as a connection point.
        5. Propose clear, specific value rather than vague collaboration ideas.
        6. The message should read as if written by a human, with natural language and appropriate tone.
        7. The structure should exactly match the example above with appropriate line breaks.
        
        This message will be sent directly to high-value contacts, so quality and personalization are critical.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are an expert in business development and networking communications."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error generating personalized message: {e}")
            # Return a basic structure in case of error
            return {
                "research_summary": [f"Information about {participant_name} from {participant_company}"],
                "synergy_points": ["Potential collaboration opportunities"],
                "message_draft": MESSAGE_TEMPLATE.format(
                    participant_name=participant_name,
                    user_name=user_name,
                    company_name=user_company_name,
                    company_short_description="",
                    personalized_intro=f"I noticed your work at {participant_company} and wanted to connect.",
                    synergy_point="I believe there might be opportunities for our companies to collaborate.",
                    user_role=user_role
                )
            }
    
    def generate_summary_report(self,
                             event_name: str,
                             total_participants: int,
                             approved_messages: int,
                             sent_messages: int,
                             message_samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary report with statistics and insights.
        
        Args:
            event_name: Name of the event
            total_participants: Total number of participants reviewed
            approved_messages: Number of messages approved
            sent_messages: Number of messages sent
            message_samples: Sample of message data to derive insights
            
        Returns:
            Dictionary with report sections
        """
        prompt = f"""
        Create a comprehensive summary report for the outreach campaign at {event_name}.
        
        STATISTICS:
        - Total Participants Reviewed: {total_participants}
        - Total Messages Approved: {approved_messages}
        - Total Messages Sent: {sent_messages}
        
        MESSAGE SAMPLES (for insight generation):
        {json.dumps(message_samples, indent=2)}
        
        Format your response as JSON with these sections:
        1. key_metrics - The statistics provided above
        2. key_learnings - 3-5 insights derived from the campaign (e.g., what worked well in messages)
        3. suggested_improvements - 3-4 specific suggestions to improve future outreach workflows
        4. success_patterns - Patterns observed in successful messages
        5. executive_summary - A brief 2-3 paragraph summary of the entire campaign
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "You are an expert in marketing analytics and business development who provides actionable insights."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse the JSON response
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error generating summary report: {e}")
            # Return a basic structure in case of error
            return {
                "key_metrics": {
                    "total_participants": total_participants,
                    "approved_messages": approved_messages,
                    "sent_messages": sent_messages
                },
                "key_learnings": ["Personalization increases engagement.", "LinkedIn insights were crucial in tailoring the synergy pitch."],
                "suggested_improvements": ["Automate LinkedIn profile fetching to speed up research."],
                "success_patterns": ["Messages with specific collaboration ideas received better responses."],
                "executive_summary": f"Summary report for {event_name} outreach campaign."
            }

# Initialize the service
def get_openai_service():
    """Get an instance of the OpenAI service."""
    return OpenAIService()
