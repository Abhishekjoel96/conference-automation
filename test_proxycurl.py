import os
import json
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Import the ProxyCurl service
from src.services.proxycurl import get_proxycurl_service

def test_proxycurl():
    """Test the ProxyCurl API integration"""
    logger.info("Testing ProxyCurl API integration")
    
    # Check if API key is present
    api_key = os.getenv('PROXYCURL_API_KEY')
    if not api_key:
        logger.error("⚠️ ProxyCurl API key not found in .env file")
        return False
    
    logger.info("✅ ProxyCurl API key found")
    
    # Initialize the ProxyCurl service
    proxycurl = get_proxycurl_service()
    
    # Test a LinkedIn profile lookup with a public profile
    test_profile_url = "https://www.linkedin.com/in/williamhgates/"
    
    try:
        logger.info(f"Testing LinkedIn profile scraping for: {test_profile_url}")
        profile_data = proxycurl.scrape_linkedin_profile(test_profile_url)
        
        if profile_data:
            logger.info(f"✅ Successfully retrieved profile data for: {profile_data.get('full_name', 'Unknown')}")
            logger.info(f"Profile headline: {profile_data.get('headline', 'N/A')}")
            logger.info(f"Current company: {profile_data.get('experiences', [{}])[0].get('company', 'N/A') if profile_data.get('experiences') else 'N/A'}")
            return True
        else:
            logger.error("❌ Failed to retrieve profile data")
            return False
    
    except Exception as e:
        logger.error(f"❌ Error during ProxyCurl test: {str(e)}")
        return False

if __name__ == "__main__":
    result = test_proxycurl()
    
    if result:
        logger.info("🎉 ProxyCurl integration test passed successfully!")
    else:
        logger.error("❌ ProxyCurl integration test failed.")
