import os
import json
import time
import random
import logging
from datetime import datetime
import requests
import cloudscraper
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Add the parent directory to the path to allow imports
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.operations import DBOperations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("team_scraper.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("team_scraper")

class TeamDataScraper:
    """
    Scraper for collecting additional team data from multiple sources
    """
    
    def __init__(self, data_dir="sofascore_data"):
        """
        Initialize the team data scraper
        
        Args:
            data_dir: Directory for storing data files
        """
        self.data_dir = data_dir
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # Create teams directory
        self.teams_dir = os.path.join(data_dir, "teams")
        if not os.path.exists(self.teams_dir):
            os.makedirs(self.teams_dir)
        
        # Initialize cloudscraper
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            delay=5
        )
        
        # User agents for requests
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0"
        ]
    
    def get_random_headers(self):
        """Generate realistic browser headers"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json, text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.sofascore.com",
            "Referer": "https://www.sofascore.com/",
            "Connection": "keep-alive"
        }
    
    def get_team_list(self, limit=50):
        """
        Get the list of teams to scrape
        
        Args:
            limit: Maximum number of teams to return
            
        Returns:
            List of team dictionaries
        """
        # First try to load teams from teams_to_scrape.json
        teams_file = os.path.join(self.data_dir, "teams_to_scrape.json")
        if os.path.exists(teams_file):
            try:
                with open(teams_file, 'r', encoding='utf-8') as f:
                    teams = json.load(f)
                
                logger.info(f"Loaded {len(teams)} teams from {teams_file}")
                return teams[:limit]
            except Exception as e:
                logger.error(f"Error loading teams from file: {str(e)}")
        
        # If file doesn't exist or there was an error, get teams from the database
        logger.info("Getting teams from database")
        teams_db = DBOperations.get_teams_needing_data(limit=limit)
        
        teams = []
        for team in teams_db:
            teams.append({
                'id': team.id,
                'name': team.name,
                'league': team.league.name if team.league else 'Unknown League',
                'country': team.country if team.country else 'Unknown'
            })
        
        logger.info(f"Got {len(teams)} teams from database")
        return teams
    
    def scrape_team_data_from_sofascore(self, team_name):
        """
        Scrape team data from SofaScore
        
        Args:
            team_name: Name of the team
            
        Returns:
            Dictionary with team data or None if failed
        """
        logger.info(f"Scraping {team_name} from SofaScore")
        
        # Format team name for URL
        team_name_formatted = team_name.lower().replace(' ', '-')
        url = f"https://www.sofascore.com/team/football/{team_name_formatted}/"
        
        try:
            # Add random delay
            time.sleep(random.uniform(2, 5))
            
            # Make request
            headers = self.get_random_headers()
            response = self.scraper.get(url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                logger.warning(f"Failed to get {team_name} from SofaScore: {response.status_code}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract team data
            team_data = {}
            
            # Try to extract stadium info
            stadium_element = soup.select_one('div:contains("Stadium")')
            if stadium_element:
                stadium_text = stadium_element.find_next('div').text.strip()
                team_data['stadium'] = stadium_text
            
            # Try to extract coach/manager
            manager_element = soup.select_one('div:contains("Manager")')
            if manager_element:
                manager_text = manager_element.find_next('div').text.strip()
                team_data['manager'] = manager_text
            
            # Try to extract founded year
            founded_element = soup.select_one('div:contains("Founded")')
            if founded_element:
                founded_text = founded_element.find_next('div').text.strip()
                try:
                    team_data['founded'] = int(founded_text)
                except ValueError:
                    team_data['founded'] = founded_text
            
            # Try to extract team description
            description_element = soup.select_one('div.description')
            if description_element:
                team_data['description'] = description_element.text.strip()
            
            team_data['source'] = 'sofascore'
            team_data['last_scraped'] = datetime.now().isoformat()
            
            return team_data
            
        except Exception as e:
            logger.error(f"Error scraping {team_name} from SofaScore: {str(e)}")
            return None
    
    def scrape_team_data_from_wikipedia(self, team_name, country=None):
        """
        Scrape team data from Wikipedia
        
        Args:
            team_name: Name of the team
            country: Country of the team (optional)
            
        Returns:
            Dictionary with team data or None if failed
        """
        logger.info(f"Scraping {team_name} from Wikipedia")
        
        search_query = f"{team_name} football club"
        if country:
            search_query += f" {country}"
        
        # Format for Wikipedia API
        search_query = search_query.replace(' ', '%20')
        url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={search_query}&limit=1&namespace=0&format=json"
        
        try:
            # Add random delay
            time.sleep(random.uniform(2, 5))
            
            # Make request to Wikipedia search
            headers = self.get_random_headers()
            response = requests.get(url, headers=headers, timeout=20)
            
            if response.status_code != 200:
                logger.warning(f"Failed to search Wikipedia for {team_name}: {response.status_code}")
                return None
            
            # Parse search results
            search_results = response.json()
            
            if len(search_results) < 4 or not search_results[3]:
                logger.warning(f"No Wikipedia page found for {team_name}")
                return None
            
            # Get the first result URL
            wiki_url = search_results[3][0]
            
            # Add random delay
            time.sleep(random.uniform(2, 5))
            
            # Get the Wikipedia page
            page_response = requests.get(wiki_url, headers=headers, timeout=20)
            
            if page_response.status_code != 200:
                logger.warning(f"Failed to get Wikipedia page for {team_name}: {page_response.status_code}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(page_response.text, 'html.parser')
            
            # Extract team data
            team_data = {}
            
            # Get infobox
            infobox = soup.select_one('.infobox')
            
            if infobox:
                # Try to extract stadium info
                stadium_row = infobox.select_one('tr:contains("Ground"), tr:contains("Stadium")')
                if stadium_row:
                    stadium_element = stadium_row.select_one('td')
                    if stadium_element:
                        team_data['stadium'] = stadium_element.text.strip()
                
                # Try to extract manager/coach
                manager_row = infobox.select_one('tr:contains("Manager"), tr:contains("Head coach"), tr:contains("Coach")')
                if manager_row:
                    manager_element = manager_row.select_one('td')
                    if manager_element:
                        team_data['manager'] = manager_element.text.strip()
                
                # Try to extract founded year
                founded_row = infobox.select_one('tr:contains("Founded")')
                if founded_row:
                    founded_element = founded_row.select_one('td')
                    if founded_element:
                        founded_text = founded_element.text.strip()
                        # Try to extract year
                        year_match = re.search(r'\b(18|19|20)\d{2}\b', founded_text)
                        if year_match:
                            team_data['founded'] = int(year_match.group(0))
                        else:
                            team_data['founded'] = founded_text
                
                # Try to extract website
                website_row = infobox.select_one('tr:contains("Website")')
                if website_row:
                    website_element = website_row.select_one('td a')
                    if website_element and website_element.has_attr('href'):
                        team_data['website'] = website_element['href']
            
            # Get team description from first paragraph
            content_paragraphs = soup.select('#mw-content-text > .mw-parser-output > p')
            for paragraph in content_paragraphs:
                if paragraph.text.strip() and not paragraph.find('span', class_='mw-empty-elt'):
                    team_data['description'] = paragraph.text.strip()
                    break
            
            team_data['source'] = 'wikipedia'
            team_data['last_scraped'] = datetime.now().isoformat()
            
            return team_data
            
        except Exception as e:
            logger.error(f"Error scraping {team_name} from Wikipedia: {str(e)}")
            return None
    
    def scrape_team_data_via_selenium(self, team_name, country=None):
        """
        Scrape team data using Selenium (fallback method)
        
        Args:
            team_name: Name of the team
            country: Country of the team (optional)
            
        Returns:
            Dictionary with team data or None if failed
        """
        logger.info(f"Scraping {team_name} using Selenium")
        
        try:
            # Set up Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
            
            # Initialize Chrome driver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Mask WebDriver to avoid detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Format search query
            search_query = f"{team_name} football club"
            if country:
                search_query += f" {country}"
            
            search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
            
            # Navigate to Google search
            driver.get(search_url)
            time.sleep(5)
            
            # Look for official website
            website_url = None
            try:
                website_element = driver.find_element(By.CSS_SELECTOR, 'a[data-dtype="d3ifr"]')
                website_url = website_element.get_attribute('href')
            except:
                try:
                    website_elements = driver.find_elements(By.CSS_SELECTOR, '.yuRUbf > a')
                    if website_elements:
                        for element in website_elements:
                            url = element.get_attribute('href')
                            if url and (team_name.lower().replace(' ', '') in url.lower() or 'official' in url.lower()):
                                website_url = url
                                break
                except:
                    pass
            
            team_data = {
                'source': 'selenium',
                'last_scraped': datetime.now().isoformat()
            }
            
            if website_url:
                team_data['website'] = website_url
                
                # Try to visit the website and get more info
                try:
                    driver.get(website_url)
                    time.sleep(5)
                    
                    # Extract page title
                    title = driver.title
                    if title:
                        team_data['official_name'] = title.strip()
                    
                    # Look for stadium info
                    for keyword in ['stadium', 'ground', 'arena']:
                        try:
                            stadium_elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{keyword}')]")
                            if stadium_elements:
                                for element in stadium_elements:
                                    try:
                                        parent = element.find_element(By.XPATH, './..')
                                        text = parent.text
                                        if keyword in text.lower() and len(text) < 100:
                                            team_data['stadium'] = text.strip()
                                            break
                                    except:
                                        continue
                        except:
                            continue
                except:
                    pass
            
            # Close the driver
            driver.quit()
            
            return team_data
            
        except Exception as e:
            logger.error(f"Error scraping {team_name} using Selenium: {str(e)}")
            return None
    
    def merge_team_data(self, data_sources):
        """
        Merge team data from multiple sources
        
        Args:
            data_sources: List of data dictionaries from different sources
            
        Returns:
            Merged team data dictionary
        """
        if not data_sources:
            return {}
        
        # Start with an empty result
        merged_data = {}
        
        # Fields to merge
        fields = ['stadium', 'manager', 'founded', 'website', 'description']
        
        # Prioritize sources: Wikipedia > SofaScore > Selenium
        priority_order = ['wikipedia', 'sofascore', 'selenium']
        
        # Sort data sources by priority
        sorted_sources = sorted(
            [ds for ds in data_sources if ds],
            key=lambda x: priority_order.index(x.get('source', 'unknown')) if x.get('source', 'unknown') in priority_order else 999
        )
        
        # Merge fields
        for field in fields:
            for source in sorted_sources:
                if field in source and source[field]:
                    merged_data[field] = source[field]
                    break
        
        # Add source information
        sources_used = [s.get('source') for s in sorted_sources if s and 'source' in s]
        if sources_used:
            merged_data['sources'] = sources_used
            
        # Add last scraped timestamp
        merged_data['last_scraped'] = datetime.now().isoformat()
        
        return merged_data
    
    def save_team_data_to_file(self, team_id, team_name, team_data):
        """
        Save team data to a JSON file
        
        Args:
            team_id: Team ID
            team_name: Team name
            team_data: Team data dictionary
            
        Returns:
            Path to the saved file
        """
        # Create filename
        filename = f"team_{team_id}_{team_name.lower().replace(' ', '_')}.json"
        file_path = os.path.join(self.teams_dir, filename)
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(team_data, f, indent=2)
        
        logger.info(f"Saved team data to {file_path}")
        return file_path
    
    def scrape_team(self, team_id, team_name, country=None):
        """
        Scrape team data from multiple sources
        
        Args:
            team_id: Team ID
            team_name: Team name
            country: Team country (optional)
            
        Returns:
            Dictionary with team data
        """
        logger.info(f"Scraping team {team_id}: {team_name}")
        
        # Track data sources
        data_sources = []
        
        # Try SofaScore
        sofascore_data = self.scrape_team_data_from_sofascore(team_name)
        if sofascore_data:
            data_sources.append(sofascore_data)
            logger.info(f"Got data from SofaScore for {team_name}")
        
        # Try Wikipedia
        wikipedia_data = self.scrape_team_data_from_wikipedia(team_name, country)
        if wikipedia_data:
            data_sources.append(wikipedia_data)
            logger.info(f"Got data from Wikipedia for {team_name}")
        
        # If no data from primary sources, try Selenium
        if not data_sources:
            selenium_data = self.scrape_team_data_via_selenium(team_name, country)
            if selenium_data:
                data_sources.append(selenium_data)
                logger.info(f"Got data from Selenium for {team_name}")
        
        # Merge data from all sources
        team_data = self.merge_team_data(data_sources)
        
        if team_data:
            # Save to file
            self.save_team_data_to_file(team_id, team_name, team_data)
            
            # Update database
            try:
                DBOperations.upsert_team_data(
                    team_id=team_id,
                    stadium=team_data.get('stadium'),
                    manager=team_data.get('manager'),
                    founded=team_data.get('founded'),
                    website=team_data.get('website'),
                    description=team_data.get('description')
                )
                logger.info(f"Updated database with team data for {team_name}")
            except Exception as e:
                logger.error(f"Error updating database for {team_name}: {str(e)}")
        
        return team_data
    
    def scrape_multiple_teams(self, limit=50, delay_min=5, delay_max=10):
        """
        Scrape data for multiple teams
        
        Args:
            limit: Maximum number of teams to scrape
            delay_min: Minimum delay between requests in seconds
            delay_max: Maximum delay between requests in seconds
            
        Returns:
            Dictionary with statistics
        """
        logger.info(f"Starting to scrape up to {limit} teams")
        
        # Get teams to scrape
        teams = self.get_team_list(limit=limit)
        
        stats = {
            "total": len(teams),
            "success": 0,
            "failed": 0,
            "start_time": datetime.now().isoformat()
        }
        
        for i, team in enumerate(teams):
            try:
                team_id = team['id']
                team_name = team['name']
                country = team.get('country')
                
                logger.info(f"Processing team {i+1}/{len(teams)}: {team_name}")
                
                # Scrape team data
                team_data = self.scrape_team(team_id, team_name, country)
                
                if team_data:
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                
                # Add delay between teams
                if i < len(teams) - 1:
                    delay = random.uniform(delay_min, delay_max)
                    logger.info(f"Waiting {delay:.2f} seconds before next team")
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error processing team: {str(e)}")
                stats["failed"] += 1
        
        stats["end_time"] = datetime.now().isoformat()
        
        # Save stats
        stats_file = os.path.join(self.data_dir, "team_scrape_stats.json")
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Team scraping completed: {stats['success']} success, {stats['failed']} failed")
        return stats


def main():
    """Main function to run the team data scraper"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Team Data Scraper')
    parser.add_argument('--limit', type=int, default=20, help='Maximum number of teams to scrape')
    parser.add_argument('--team-id', type=int, help='Scrape a specific team by ID')
    parser.add_argument('--team-name', type=str, help='Scrape a specific team by name')
    
    args = parser.parse_args()
    
    scraper = TeamDataScraper()
    
    if args.team_id and args.team_name:
        # Scrape a specific team
        team_id = args.team_id
        team_name = args.team_name
        
        print(f"Scraping team {team_id}: {team_name}")
        team_data = scraper.scrape_team(team_id, team_name)
        
        if team_data:
            print(f"Successfully scraped {team_name}")
            print(json.dumps(team_data, indent=2))
        else:
            print(f"Failed to scrape {team_name}")
    else:
        # Scrape multiple teams
        limit = args.limit
        print(f"Scraping up to {limit} teams")
        
        stats = scraper.scrape_multiple_teams(limit=limit)
        
        print("\n=== Team Scraping Summary ===")
        print(f"Total Teams: {stats['total']}")
        print(f"Successful: {stats['success']}")
        print(f"Failed: {stats['failed']}")


if __name__ == "__main__":
    main()