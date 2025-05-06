import requests
import json
import logging
from ..config import PROXYCURL_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProxyCurlService:
    def __init__(self):
        self.api_key = PROXYCURL_API_KEY
        self.base_url = "https://nubela.co/proxycurl/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    def scrape_linkedin_profile(self, linkedin_url, **kwargs):
        """
        Scrape a LinkedIn profile using ProxyCurl API.
        
        Args:
            linkedin_url: URL of the LinkedIn profile to scrape
            
        Returns:
            Dictionary with structured LinkedIn profile data or None if scraping failed
        """
        if not linkedin_url:
            logger.error("No LinkedIn URL provided for scraping.")
            return None
        
        endpoint = f"{self.base_url}/v2/linkedin"
        params = {
            "url": linkedin_url,
            "use_cache": "if-present"
        }
        
        logger.info(f"Scraping LinkedIn profile: {linkedin_url}")
        
        try:
            response = requests.get(
                endpoint,
                params=params,
                headers=self.headers
            )
            
            if response.status_code == 200:
                profile_data = response.json()
                logger.info(f"Successfully scraped LinkedIn profile for {profile_data.get('full_name', 'Unknown')}")
                return profile_data
            else:
                logger.error(f"Failed to scrape LinkedIn profile. Status code: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception occurred while calling ProxyCurl API: {str(e)}")
            return None
    
    def scrape_company_profile(self, linkedin_company_url, **kwargs):
        """
        Scrape a LinkedIn company profile using ProxyCurl API.
        
        Args:
            linkedin_company_url: URL of the LinkedIn company profile to scrape
            
        Returns:
            Dictionary with structured company data or None if scraping failed
        """
        if not linkedin_company_url:
            logger.error("No LinkedIn company URL provided for scraping.")
            return None
        
        endpoint = f"{self.base_url}/v2/company"
        params = {
            "url": linkedin_company_url,
            "use_cache": "if-present"
        }
        
        logger.info(f"Scraping LinkedIn company: {linkedin_company_url}")
        
        try:
            response = requests.get(
                endpoint,
                params=params,
                headers=self.headers
            )
            
            if response.status_code == 200:
                company_data = response.json()
                logger.info(f"Successfully scraped LinkedIn company profile for {company_data.get('name', 'Unknown')}")
                return company_data
            else:
                logger.error(f"Failed to scrape LinkedIn company profile. Status code: {response.status_code}, Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Exception occurred while calling ProxyCurl API: {str(e)}")
            return None

    def scrape_conference_participants(self, conference_url, login_credentials=None, **kwargs):
        """
        Note: ProxyCurl doesn't directly scrape conference websites.
        This is a stub function that returns an empty list.
        You would need to implement a different solution for conference scraping.
        
        Args:
            conference_url: URL of the conference website
            login_credentials: Optional dictionary with username and password for protected sites
            
        Returns:
            Empty list as ProxyCurl doesn't support conference scraping
        """
        logger.warning("ProxyCurl doesn't support conference website scraping. Returning empty list.")
        return []

# Initialize the service
def get_proxycurl_service():
    """Get an instance of the ProxyCurl service."""
    return ProxyCurlService()
