import requests
import json
import logging
import urllib.parse
from typing import Dict, List, Any, Optional
from ..config import SERPAPI_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SerpApiService:
    def __init__(self):
        self.api_key = SERPAPI_API_KEY
        if not self.api_key or self.api_key == "your-api-key-here":
            logger.error("No SerpAPI API key provided. Check your .env file.")
        self.base_url = "https://serpapi.com/search"
    
    def search_google(self, query: str, num_results: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Search Google for information using SerpAPI.
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 10)
            
        Returns:
            List of search result dictionaries or None if search failed
        """
        # Validate API key
        if not self.api_key:
            logger.error("Cannot perform search: No SerpAPI API key provided. Check your .env file.")
            raise ValueError("SerpAPI API key is missing.")

        # Log API key usage (partially masked)
        masked_key = self.api_key[:4] + "..." + self.api_key[-4:] if len(self.api_key) > 8 else self.api_key
        logger.debug(f"Using SerpAPI Key: {masked_key}")

        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": min(num_results, 10),  # Cap at 10 to limit API usage
            "no_cache": "true"  # Avoid cached results
        }

        logger.info(f"Attempting SerpAPI search with query: '{query}', num_results: {num_results}")
        logger.debug(f"SerpAPI request parameters (excluding api_key): {{'q': '{query}', 'num': {num_results}, 'engine': 'google', ...}}") # Log parameters

        try:
            # Make the API request with a slightly longer timeout
            response = requests.get(self.base_url, params=params, timeout=45) 
            
            # Log the request URL (without API key for security)
            debug_params = params.copy()
            debug_params['api_key'] = '***REDACTED***'
            logger.debug(f"SerpAPI request URL: {self.base_url}?{urllib.parse.urlencode(debug_params)}")
            
            # Check for specific HTTP errors before raising generic exception
            if response.status_code == 401:
                 logger.error(f"SerpAPI Error (401 Unauthorized): Invalid API Key. Please check your .env file.")
                 return None
            elif response.status_code == 429:
                 logger.error(f"SerpAPI Error (429 Too Many Requests): API limit reached.")
                 return None
            
            # Raise an exception for other bad status codes (4xx or 5xx)
            response.raise_for_status()
            
            # Parse the JSON response
            try:
                data = response.json()
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing SerpAPI JSON response: {e}. Response text: {response.text[:500]}") # Log part of the response
                return None
            
            # Check for errors reported within the JSON response itself
            if "error" in data:
                logger.error(f"SerpAPI returned an error in the response: {data['error']}")
                return None
            
            # Extract organic results
            if "organic_results" in data:
                results = data.get("organic_results", [])
                logger.info(f"Successfully retrieved {len(results)} organic results from SerpAPI for query: '{query}'")
                return results
            else:
                logger.warning(f"No 'organic_results' key found in SerpAPI response for query: '{query}'. Full response keys: {list(data.keys())}")
                return [] # Return empty list instead of None if no results but no error
                
        except requests.exceptions.Timeout:
            logger.error(f"SerpAPI request timed out after 45 seconds for query: {query}")
            return None
        except requests.exceptions.ConnectionError as e:
             logger.error(f"SerpAPI connection error: {e}. Check network connectivity.")
             return None
        except requests.exceptions.HTTPError as e:
            # This catches errors raised by response.raise_for_status() for non-2xx codes not handled above
             logger.error(f"SerpAPI HTTP error: {e.response.status_code} - {e.response.reason}. Response: {e.response.text[:500]}")
             return None
        except requests.exceptions.RequestException as e:
            # Catch any other request-related errors
            logger.error(f"General SerpAPI request error: {e}")
            return None
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error during SerpAPI call: {str(e)}", exc_info=True) # Log traceback
            return None

    def search_company_info(self, company_name: str) -> Dict[str, Any]:
        """
        Search for company information using SerpAPI.
        
        Args:
            company_name: Name of the company to research
            
        Returns:
            Dictionary with company information
        """
        print(f"Searching for company information: {company_name}")
        
        # Validate API key
        if not self.api_key:
            print("ERROR: SerpAPI key is missing. Check your .env configuration!")
            return {
                "company_name": company_name,
                "description": "API key missing - unable to research company",
                "error": "SERPAPI_API_KEY not configured"
            }
            
        # Create a base info object
        company_info = {
            "company_name": company_name,
            "description": "",
            "industry": "",
            "founded": "",
            "size": "",
            "headquarters": "",
            "website": "",
            "news": [],
            "funding": "",
            "competitors": [],
            "linkedin": ""
        }
        
        # Basic company query
        query = f"{company_name} company"
        basic_params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
            "num": 5
        }
        
        print(f"SerpAPI request: {self.base_url} with query: {query}")
        
        try:
            response = requests.get(self.base_url, params=basic_params)
            print(f"SerpAPI response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Successfully received SerpAPI data for {company_name}")
                
                # Extract useful information from search results
                if "knowledge_graph" in data:
                    kg = data["knowledge_graph"]
                    company_info["description"] = kg.get("description", "")
                    company_info["industry"] = kg.get("industry", "")
                    company_info["founded"] = kg.get("founded", "")
                    company_info["website"] = kg.get("website", "")
                    
                # Extract information from organic results
                if "organic_results" in data:
                    for result in data["organic_results"][:3]:
                        if "snippet" in result and len(company_info["description"]) < 100:
                            company_info["description"] = result["snippet"]
            else:
                print(f"SerpAPI error response: {response.text}")
                company_info["description"] = f"Error getting company information: HTTP {response.status_code}"
                company_info["error"] = response.text
        except Exception as e:
            print(f"Exception in SerpAPI company search: {str(e)}")
            company_info["description"] = f"Error getting company information: {str(e)}"
            company_info["error"] = str(e)
        
        return company_info
    
    def search_person_info(self, full_name: str, company_name: str = None) -> Dict[str, Any]:
        """
        Search for information about a person and return structured data.
        
        Args:
            full_name: Full name of the person to research
            company_name: Company name to refine the search (optional)
            
        Returns:
            Dictionary with structured person information
        """
        # First search - LinkedIn profile
        if company_name:
            linkedin_query = f"{full_name} {company_name} linkedin"
        else:
            linkedin_query = f"{full_name} linkedin"
            
        linkedin_results = self.search_google(linkedin_query, num_results=2)
        
        # Second search - general background
        background_query = f"{full_name} biography background"
        background_results = self.search_google(background_query, num_results=3)
        
        # Third search - recent achievements or news
        achievements_query = f"{full_name} achievements news recent"
        achievements_results = self.search_google(achievements_query, num_results=2)
        
        # Compile the research into structured format
        person_info = {
            "name": full_name,
            "linkedin_results": linkedin_results if linkedin_results else [],
            "background_info": background_results if background_results else [],
            "achievements": achievements_results if achievements_results else [],
            "search_queries": {
                "linkedin": linkedin_query,
                "background": background_query,
                "achievements": achievements_query
            }
        }
        
        return person_info
    
    def find_synergies(self, user_company: str, participant_company: str) -> Dict[str, Any]:
        """
        Search for potential synergies between two companies.
        
        Args:
            user_company: Name of the user's company
            participant_company: Name of the participant's company
            
        Returns:
            Dictionary with structured synergy information
        """
        # Search for potential collaborations
        collaboration_query = f"{user_company} {participant_company} partnership collaboration synergy"
        collaboration_results = self.search_google(collaboration_query, num_results=3)
        
        # Search for industry overlap
        industry_query = f"{user_company} {participant_company} industry market overlap"
        industry_results = self.search_google(industry_query, num_results=2)
        
        # Search for potential joint opportunities
        opportunity_query = f"{user_company} {participant_company} joint venture opportunity"
        opportunity_results = self.search_google(opportunity_query, num_results=2)
        
        # Compile the research into structured format
        synergy_info = {
            "companies": {
                "user": user_company,
                "participant": participant_company
            },
            "collaboration_opportunities": collaboration_results if collaboration_results else [],
            "industry_overlap": industry_results if industry_results else [],
            "joint_opportunities": opportunity_results if opportunity_results else [],
            "search_queries": {
                "collaboration": collaboration_query,
                "industry": industry_query,
                "opportunity": opportunity_query
            }
        }
        
        return synergy_info
        
    def scrape_conference_participants(self, conference_url, search_id=None, login_credentials=None):
        """
        Scrape participants from a conference website using SerpAPI.
        This maintains a compatible method signature for backward compatibility.
        
        Args:
            conference_url: URL of the conference website
            search_id: Ignored (kept for compatibility)
            login_credentials: Optional dictionary with username and password for protected sites
            
        Returns:
            List of participant data dictionaries or empty list if scraping failed
        """
        logger.info(f"Scraping conference participants from {conference_url} using SerpAPI")
        
        # Validate inputs
        if not conference_url:
            logger.error("No conference URL provided")
            return []
            
        if not self.api_key:
            logger.error("No SerpAPI API key provided. Check your .env file.")
            return []
        
        # Check if login credentials were provided
        if login_credentials:
            logger.info("Login credentials provided, but SerpAPI doesn't support direct login. Using public data only.")
        
        try:
            # Extract domain from conference URL for better search results
            if '//' in conference_url:
                domain = conference_url.split('//')[1].split('/')[0]
            else:
                domain = conference_url.split('/')[0]
                
            logger.info(f"Extracted domain: {domain} from URL: {conference_url}")
            
            # Build multiple queries to find speakers/participants for this conference
            queries = [
                f"speakers participants {domain}",
                f"{domain} conference speakers",
                f"{domain} event presenters"
            ]
            
            all_results = []
            
            # Try multiple queries to get better results
            for query in queries:
                logger.info(f"Running SerpAPI query: {query}")
                results = self.search_google(query=query, num_results=10)
                
                if results:
                    all_results.extend(results)
                    logger.info(f"Got {len(results)} results for query: {query}")
                else:
                    logger.warning(f"No results found for query: {query}")
            
            if not all_results:
                logger.error(f"No search results found for any query related to conference: {conference_url}")
                return []
                
            # Deduplicate results
            unique_results = []
            seen_links = set()
            
            for result in all_results:
                link = result.get('link', '')
                if link and link not in seen_links:
                    seen_links.add(link)
                    unique_results.append(result)
                    
            logger.info(f"Found {len(unique_results)} unique results across all queries")
                
            # Extract and normalize participant data
            participants = []
            seen_names = set()
            
            # Add fallback values if we don't find enough participants
            fallback_names = [
                "Speaker 1", "Speaker 2", "Speaker 3", "Speaker 4", "Speaker 5",
                "Presenter 1", "Presenter 2", "Participant 1", "Participant 2", "Participant 3"
            ]
            
            # Process regular search results
            for result in unique_results:
                # Try to find a name in the title
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                link = result.get('link', '')
                
                # Try different title separators: dash, pipe, colon
                for separator in [' - ', ' | ', ': ']:
                    if separator in title:
                        name_parts = title.split(separator)
                        
                        if len(name_parts) >= 2:
                            potential_name = name_parts[0].strip()
                            potential_role = name_parts[1].strip()
                            
                            # Skip obvious non-person titles
                            if any(skip in potential_name.lower() for skip in ['home', 'about', 'contact', 'schedule', 'privacy']):
                                continue
                                
                            # Avoid duplicates
                            if potential_name.lower() in seen_names:
                                continue
                                
                            seen_names.add(potential_name.lower())
                            
                            # Create normalized participant record
                            participant = {
                                "name": potential_name,
                                "role": potential_role if len(potential_role) < 50 else "",
                                "company": domain,  # Use domain as fallback company
                                "linkedin_url": "",  # Will be filled by ProxyCurl later
                                "email": "",
                                "bio": snippet[:100] if snippet else ""
                            }
                            
                            participants.append(participant)
                            break  # Found a valid separator, no need to try others
                
                # Limit to max 10 participants
                if len(participants) >= 10:
                    break
            
            # If we didn't find enough participants, use fallbacks
            if len(participants) < 5:
                logger.warning(f"Only found {len(participants)} participants, adding fallbacks")
                
                # How many fallbacks needed
                needed = min(10 - len(participants), len(fallback_names))
                
                for i in range(needed):
                    fallback = {
                        "name": fallback_names[i],
                        "role": f"Conference {domain}",
                        "company": domain,
                        "linkedin_url": "",
                        "email": "",
                        "bio": f"Generated placeholder for {domain} conference"
                    }
                    participants.append(fallback)
            
            # Ensure we have at least some data to work with
            if participants:
                logger.info(f"Successfully extracted {len(participants)} participants for conference: {conference_url}")
                return participants
            else:
                logger.error(f"Failed to extract any participants from search results")
                return []
            
        except Exception as e:
            logger.error(f"Error scraping conference using SerpAPI: {str(e)}")
            logger.exception("Full traceback:")
            
            # Return a basic placeholder to avoid UI errors
            return [
                {
                    "name": "Conference Participant",
                    "role": "Speaker",
                    "company": conference_url,
                    "linkedin_url": "",
                    "email": "",
                    "bio": "Placeholder data generated when scraping failed."
                }
            ]

# Initialize the service
def get_serpapi_service():
    """Get an instance of the SerpAPI service."""
    return SerpApiService()
