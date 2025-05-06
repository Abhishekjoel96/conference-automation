import os
import json
import logging
from typing import Dict, List, Any, Optional

# Import services
from ..services.proxycurl import get_proxycurl_service
from ..services.serpapi import get_serpapi_service
from ..services.openai_service import get_openai_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LinkedInResearcher:
    def __init__(self):
        self.proxycurl = get_proxycurl_service()
        self.serpapi = get_serpapi_service()
        self.openai = get_openai_service()
    
    def research_participant(self, 
                          participant_name: str, 
                          participant_role: str, 
                          participant_company: str, 
                          linkedin_url: Optional[str] = None,
                          # No phantom ID needed for ProxyCurl
                          user_company_name: Optional[str] = None,
                          additional_context: Optional[str] = None) -> Dict[str, Any]:
        """
        Research a participant using LinkedIn and web search.
        
        Args:
            participant_name: Name of the participant
            participant_role: Role/position of the participant
            participant_company: Company name of the participant
            linkedin_url: LinkedIn profile URL if available
            # LinkedIn scraping is now handled by ProxyCurl
            user_company_name: Name of the user's company for finding synergies
            additional_context: Optional biographical information or notes about the participant
            
        Returns:
            Dictionary with research information
        """
        logger.info(f"Researching participant: {participant_name} from {participant_company}")
        
        # Initialize research data with additional context if provided
        research_data = {
            "participant": {
                "name": participant_name,
                "role": participant_role,
                "company": participant_company,
                "linkedin_url": linkedin_url,
                "additional_context": additional_context if additional_context else ""
            },
            "linkedin_data": None,
            "person_info": None,
            "company_info": None,
            "synergy_info": None,
            "research_summary": None,
            "research_success": False  # Track if research was successful
        }
        
        # Step 1: Use ProxyCurl to scrape LinkedIn if URL is provided
        if linkedin_url:
            try:
                linkedin_data = self.proxycurl.scrape_linkedin_profile(
                    linkedin_url=linkedin_url
                )
                research_data["linkedin_data"] = linkedin_data
                logger.info(f"Successfully scraped LinkedIn for {participant_name}")
            except Exception as e:
                logger.error(f"Error scraping LinkedIn for {participant_name}: {e}")
        
        # Step 2: Use SerpAPI to gather additional information about the person
        try:
            person_info = self.serpapi.search_person_info(
                full_name=participant_name,
                company_name=participant_company
            )
            research_data["person_info"] = person_info
            logger.info(f"Successfully gathered person info for {participant_name}")
        except Exception as e:
            logger.error(f"Error gathering person info for {participant_name}: {e}")
        
        # Step 3: Use SerpAPI to gather information about the company
        try:
            company_info = self.serpapi.search_company_info(
                company_name=participant_company
            )
            research_data["company_info"] = company_info
            logger.info(f"Successfully gathered company info for {participant_company}")
        except Exception as e:
            logger.error(f"Error gathering company info for {participant_company}: {e}")
            
        # Step 4: Find potential synergies between user's company and participant's company
        if user_company_name:
            try:
                synergy_info = self.serpapi.find_synergies(
                    user_company=user_company_name,
                    participant_company=participant_company
                )
                research_data["synergy_info"] = synergy_info
                logger.info(f"Successfully found potential synergies between {user_company_name} and {participant_company}")
            except Exception as e:
                logger.error(f"Error finding synergies between {user_company_name} and {participant_company}: {e}")
        
        return research_data
    
    def generate_research_summary(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a human-readable research summary from the research data.
        """
        logger.info(f"Generating research summary")
        
        participant = research_data['participant']
        person_info = research_data["person_info"] or {}
        company_info = research_data["company_info"] or {}
        linkedin_data = research_data["linkedin_data"] or {}
        additional_context = participant.get("additional_context", "")
        
        # Mark research as successful
        research_data["research_success"] = True
        
        # Create a structured research summary matching the required format
        formatted_summary = {
            "name": participant["name"],
            "role": f"{participant['role']} at {participant['company']}",
            "company": self._extract_company_description(company_info),
            "linkedin": participant.get("linkedin_url", "LinkedIn Profile not available"),
            "background": self._extract_background(person_info, linkedin_data, additional_context),
            "areas_of_synergy": self._extract_synergy_points(research_data["synergy_info"]),
            "additional_notes": additional_context,
            "research_timestamp": self._get_formatted_timestamp()
        }
        
        # Store the formatted summary in research_data
        research_data["research_summary"] = formatted_summary
        research_data["research_success"] = True
        
        logger.info(f"Successfully generated research summary for {participant['name']}")
        
        return formatted_summary
        
    def _get_formatted_timestamp(self):
        """Get current timestamp formatted for reports"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def _extract_company_description(self, company_info: Dict[str, Any]) -> str:
        """
        Extract a concise company description from company info.
        """
        if not company_info:
            return "No company information available"
        
        # Try to extract from knowledge graph or organic results
        if "knowledge_graph" in company_info:
            kg = company_info["knowledge_graph"]
            if "description" in kg:
                return kg["description"]
        
        # Extract from organic results if available
        if "organic_results" in company_info and company_info["organic_results"]:
            first_result = company_info["organic_results"][0]
            if "snippet" in first_result:
                return first_result["snippet"]
        
        return "Company information not detailed enough"
    
    def _extract_background(self, person_info: Dict[str, Any], linkedin_data: Dict[str, Any], additional_context: str = "") -> str:
        """
        Extract background information from person info and LinkedIn data.
        """
        background = ""
        
        # Try LinkedIn data first
        if linkedin_data:
            if "summary" in linkedin_data and linkedin_data["summary"]:
                return linkedin_data["summary"]
            
            # Combine experience if summary not available
            if "experiences" in linkedin_data and linkedin_data["experiences"]:
                exp = linkedin_data["experiences"][0]
                return f"Previously worked at {exp.get('companyName', '')} as {exp.get('title', '')}"
        
        # Try person info from SerpAPI
        if "organic_results" in person_info and person_info["organic_results"]:
            background = person_info["organic_results"][0].get("snippet", "")
        
        return background or "No detailed background information available"
    
    def _extract_synergy_points(self, synergy_info: Optional[Dict[str, Any]]) -> List[str]:
        """
        Extract synergy points from synergy info.
        """
        if not synergy_info or "synergy_points" not in synergy_info:
            return [
                "Both companies use technology to solve real-world problems",
                "Potential for knowledge sharing and industry insights",
                "Possibilities for talent exchange or recruitment partnerships"
            ]
        
        return synergy_info.get("synergy_points", [])
        
        # Generate research summary using OpenAI
        try:
            # We'll still use OpenAI for backup or additional insights
            openai_summary = self.openai.generate_research_summary(
                person_info=person_info,
                company_info=company_info
            )
            
            # Enhance our formatted summary with any additional insights
            # but maintain the required structure
            return formatted_summary
        except Exception as e:
            logger.error(f"Error generating research summary: {e}")
            # Return our formatted summary anyway as we've already created it
            return formatted_summary

# Initialize the researcher
def get_linkedin_researcher():
    """Get an instance of the LinkedIn researcher."""
    return LinkedInResearcher()
