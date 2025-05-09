from nlp_utils import load_spacy_model, extract_skills_from_text
import requests
from bs4 import BeautifulSoup
import spacy
from urllib.parse import urljoin
import time
import random
import os # For checking if model path exists, though spacy.load handles it
# Import database functions
from database_manager import init_db, save_job_to_db
import sys

# Add the current directory to the path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import the NLP utilities
from nlp_utils import load_spacy_model, extract_skills_from_text

# --- spaCy Model Loading ---
# Load spaCy model and skill keywords at the module level
nlp_model, skill_keywords = load_spacy_model()

def fetch_page(url, params=None, retries=3, delay=5):
    """Fetches HTML content from a URL with retries and headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 JobScraper/1.0 (cody@sourcegraph.com)'
    }
    for attempt in range(retries):
        try:
            print(f"    Fetching URL: {url} with params: {params}") # Added for clarity
            response = requests.get(url, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            print(f"    HTTP error fetching {url} (attempt {attempt + 1}/{retries}): {e.response.status_code} {e.response.reason}")
            if e.response.status_code in [404, 403, 410]: # 410 Gone
                print(f"    Page not found/forbidden/gone ({e.response.status_code}). Skipping this URL.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"    Error fetching {url} (attempt {attempt + 1}/{retries}): {e}")
            
        if attempt < retries - 1:
            actual_delay = delay + random.uniform(0, delay * 0.5)
            print(f"    Retrying in {actual_delay:.2f} seconds...")
            time.sleep(actual_delay)
        else:
            print(f"    Failed to fetch {url} after {retries} attempts.")
    return None

def parse_job_detail_page_adzuna(full_job_url):
    print(f"    Fetching details from Adzuna landing page: {full_job_url}")
    html_content = fetch_page(full_job_url) # No params needed here
    if not html_content:
        print(f"    Failed to fetch detail page content for {full_job_url}")
        return "Could not fetch detail page content.", "Adzuna"

    soup = BeautifulSoup(html_content, 'html.parser')
    site_name = "Adzuna" # Default
    
    # Try to find the "redirecting to" message if it exists
    redirect_message_h2 = soup.find('h2', string=lambda t: t and "you are being redirected to" in t.lower())
    if redirect_message_h2 and redirect_message_h2.strong:
        site_name_from_page = redirect_message_h2.strong.text.strip()
        # We could use site_name_from_page, but for now, let's stick to Adzuna as the platform
        # as the job data itself (snippet) comes from Adzuna's listing.
        # print(f"    Adzuna redirecting to: {site_name_from_page}")

    return "Full description not found on Adzuna landing page (this is expected).", site_name

def scrape_adzuna_jobs(query="python developer", location="bangalore", pages=1): # We'll change the default query in main_adzuna
    print(f"Starting Adzuna scrape for '{query}' in '{location}' for {pages} page(s).")
    base_url = "https://www.adzuna.in/search" # Adzuna's base search URL
    
    for page_num in range(1, pages + 1):
        params = {
            'q': query,
            'w': location,
            'p': page_num
        }
        print(f"\nScraping Adzuna page {page_num}...")
        html_content = fetch_page(base_url, params=params)
        if not html_content:
            print(f"Failed to fetch Adzuna search results page {page_num}. Skipping.")
            continue

        soup = BeautifulSoup(html_content, 'html.parser')
        
        # --- NEW SELECTOR FOR JOB LISTINGS ---
        # Based on: <article class="a flex gap-2 md:gap-4 p-3 md:pb-1 border-b ...">
        # A simpler selector might be 'article.a' if 'a' is a unique enough class for job articles
        # Or more specific: 'article[class*="border-b"]' if that's consistent for jobs
        # Let's try the one suggested, but be mindful it might be too specific if classes change slightly
        job_listings = soup.select('article.a.flex.gap-2') 
        
        # A slightly more robust alternative if the above is too brittle:
        # job_listings = soup.find_all('article', class_=lambda c: c and 'border-b' in c and 'cursor-pointer' in c)

        if not job_listings:
            print(f"No job listings found on page {page_num} with current selectors. Adzuna's HTML might have changed or no results for query.")
            # Optional: print a snippet of the HTML to help debug if it fails
            # print(soup.prettify()[:2000]) 
            break 

        print(f"Found {len(job_listings)} potential job listings on page {page_num}.")

        for job_ad in job_listings:
            # --- NEW SELECTORS FOR INDIVIDUAL ELEMENTS ---
            # Title & URL: <a class="text-base md:text-xl lg:text-2xl text-adzuna-green-500 hover:underline" href="...">
            title_tag = job_ad.select_one('h2 a[href]') # Ensure it's an 'a' tag with an href inside an h2
            if not title_tag: # Fallback if h2 > a structure changes
                title_tag = job_ad.select_one('a[class*="text-adzuna-green-500"][href]')

            # Company Name: <div class="ui-company">
            company_tag = job_ad.select_one('div.ui-company')
            company = company_tag.text.strip() if company_tag else "N/A"

            # Location: <div class="ui-location text-adzuna-gray-900">
            location_tag = job_ad.select_one('div.ui-location')
            job_location = location_tag.text.strip() if location_tag else "N/A"

            # Description Snippet: <div class="max-snippet-height md:overflow-hidden"> or <div class="hidden sm:block"><span>...</span></div>
            # The provided selector was: '.hidden.sm\\:block span'
            # The backslash for ':' is for CSS, BeautifulSoup might not need it or handle it differently.
            # Let's try a few options for robustness.
            description_snippet_tag = job_ad.select_one('div.max-snippet-height span') # If span is direct child
            if not description_snippet_tag:
                description_snippet_tag = job_ad.select_one('div.max-snippet-height') # Take the div text if span not found
            if not description_snippet_tag: 
                # Try the AI's suggestion, being careful with sm:block
                # For classes like "sm:block", use "sm\:block" in CSS selectors if using querySelector in browser.
                # In BeautifulSoup, you can often select by parts of the class or use a function.
                # Let's try finding a div that has 'hidden' and 'sm:block' (or contains 'block') and then its span
                desc_container = job_ad.find('div', class_=lambda c: c and 'hidden' in c and 'block' in c)
                if desc_container:
                    description_snippet_tag = desc_container.find('span')

            description_snippet = description_snippet_tag.text.strip() if description_snippet_tag else "No snippet available."
            
            job_url = None
            if title_tag and title_tag.has_attr('href'):
                job_url = title_tag['href']
                title = title_tag.get_text(strip=True) # Use get_text() for robustness
            else:
                title = "N/A"

            if title != "N/A" and job_url:
                # Adzuna URLs in search results are often full URLs to their /land/ad/ page
                # If they are relative, urljoin will handle it.
                # The base_url for urljoin should be the domain, not the search path.
                adzuna_domain_base = "https://www.adzuna.in"
                full_job_url = urljoin(adzuna_domain_base, job_url)
                
                print(f"\n  Processing job: {title} at {company}")
                print(f"    Location: {job_location}")
                print(f"    Snippet: {description_snippet[:100]}...") # Show only first 100 chars
                print(f"    Adzuna link: {full_job_url}")

                platform_name = "Adzuna"
                final_description = description_snippet # Using snippet as the main description for now
                
                # Extract skills from the description using NLP
                skills = extract_skills_from_text(final_description, nlp_model, skill_keywords)
                
                print(f"    Extracted Skills (from snippet): {skills if skills else 'None found'}")

                job_data = {
                    'title': title,
                    'company': company,
                    'location': job_location,
                    'description': final_description,
                    'source_url': full_job_url,
                    'skills': skills,
                    'platform': platform_name
                }
                
                save_job_to_db(job_data)
            else:
                print("    Could not find title or job URL for a listing. Skipping.")
                
            time.sleep(random.uniform(1.5, 4))
             
        if not job_listings: # This check is after the loop, should be before if we want to break early
            break # Already handled above, but good for clarity

        print(f"Finished page {page_num}. Sleeping before next page...")
        time.sleep(random.uniform(4, 8))

    print("\nAdzuna scraping complete. Data saved to database.")

def main_adzuna(query, location, pages=1):
    # No need to check if spaCy model is loaded since we load it at the module level
    print(f"Starting job scraping for Adzuna: '{query}' in '{location}' for {pages} page(s).") # Use the parameters
    scrape_adzuna_jobs(query=query, location=location, pages=pages) # Pass the parameters along
    print("\nAdzuna scraping complete. Data saved to database.") # More specific message
    
    #print("\nAll scraping finished.")

if __name__ == '__main__':
    init_db() # Initialize the database ONCE here
    DEFAULT_QUERY = "python developer"
    DEFAULT_LOCATION = "bangalore" 
    DEFAULT_PAGES = 1
    print(f"Preparing to scrape Adzuna for query='{DEFAULT_QUERY}', location='{DEFAULT_LOCATION}', pages={DEFAULT_PAGES}")
    main_adzuna(query=DEFAULT_QUERY, location=DEFAULT_LOCATION, pages=DEFAULT_PAGES)
    print("All scraping finished.") # This is the final message
