from nlp_utils import load_spacy_model, extract_skills_from_text
import requests
from bs4 import BeautifulSoup
import spacy
from urllib.parse import urljoin
import time
import random
import os
from database_manager import init_db, save_job_to_db
import sys
import io
import argparse  # Add this for command line arguments

# Set stdout to handle Unicode properly
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add the current directory to the path to ensure imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

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
            print(f"    Fetching URL: {url} with params: {params}")
            response = requests.get(url, headers=headers, params=params, timeout=20)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            print(f"    HTTP error fetching {url} (attempt {attempt + 1}/{retries}): {e.response.status_code} {e.response.reason}")
            if e.response.status_code in [404, 403, 410]:
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
    html_content = fetch_page(full_job_url)
    if not html_content:
        print(f"    Failed to fetch detail page content for {full_job_url}")
        return "Could not fetch detail page content.", "Adzuna"
        
    soup = BeautifulSoup(html_content, 'html.parser')
    site_name = "Adzuna"
        
    redirect_message_h2 = soup.find('h2', string=lambda t: t and "you are being redirected to" in t.lower())
    if redirect_message_h2 and redirect_message_h2.strong:
        site_name_from_page = redirect_message_h2.strong.text.strip()
        return "Full description not found on Adzuna landing page (this is expected).", site_name

def scrape_adzuna_jobs(query="All", location="All", pages=1):
    print(f"Starting Adzuna scrape for '{query}' in '{location}' for {pages} page(s).")
    
    # Handle the "All" value for query and location
    search_query = "" if query.lower() == "all" else query
    search_location = "" if location.lower() == "all" else location
    
    print(f"Using search query: '{search_query}' and location: '{search_location}'")
    
    base_url = "https://www.adzuna.in/search"
        
    for page_num in range(1, pages + 1):
        params = {}
        
        # Only add parameters if they have values
        if search_query:
            params['q'] = search_query
        if search_location:
            params['w'] = search_location
            
        params['p'] = page_num
        
        print(f"\nScraping Adzuna page {page_num}...")
        html_content = fetch_page(base_url, params=params)
        if not html_content:
            print(f"Failed to fetch Adzuna search results page {page_num}. Skipping.")
            continue
            
        soup = BeautifulSoup(html_content, 'html.parser')
            
        job_listings = soup.select('article.a.flex.gap-2')
            
        if not job_listings:
            print(f"No job listings found on page {page_num} with current selectors. Adzuna's HTML might have changed or no results for query.")
            break
            
        print(f"Found {len(job_listings)} potential job listings on page {page_num}.")
        for job_ad in job_listings:
            title_tag = job_ad.select_one('h2 a[href]')
            if not title_tag:
                title_tag = job_ad.select_one('a[class*="text-adzuna-green-500"][href]')
                
            company_tag = job_ad.select_one('div.ui-company')
            company = company_tag.text.strip() if company_tag else "N/A"
                
            location_tag = job_ad.select_one('div.ui-location')
            job_location = location_tag.text.strip() if location_tag else "N/A"
                
            description_snippet_tag = job_ad.select_one('div.max-snippet-height span')
            if not description_snippet_tag:
                description_snippet_tag = job_ad.select_one('div.max-snippet-height')
            if not description_snippet_tag:
                desc_container = job_ad.find('div', class_=lambda c: c and 'hidden' in c and 'block' in c)
                if desc_container:
                    description_snippet_tag = desc_container.find('span')
                
            description_snippet = description_snippet_tag.text.strip() if description_snippet_tag else "No snippet available."
                
            job_url = None
            if title_tag and title_tag.has_attr('href'):
                job_url = title_tag['href']
                title = title_tag.get_text(strip=True)
            else:
                title = "N/A"
                
            if title != "N/A" and job_url:
                adzuna_domain_base = "https://www.adzuna.in"
                full_job_url = urljoin(adzuna_domain_base, job_url)
                
                print(f"\n  Processing job: {title} at {company}")
                print(f"    Location: {job_location}")
                
                # Safely print the snippet with handling for Unicode characters
                try:
                    print(f"    Snippet: {description_snippet[:100]}...")
                except UnicodeEncodeError:
                    # If encoding fails, replace problematic characters with '?'
                    safe_snippet = description_snippet[:100].encode('ascii', 'replace').decode('ascii')
                    print(f"    Snippet: {safe_snippet}...")
                
                print(f"    Adzuna link: {full_job_url}")
                
                platform_name = "Adzuna"
                final_description = description_snippet
                
                # Extract skills from description
                skills = extract_skills_from_text(final_description, nlp_model)
                
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
                
        print(f"Finished page {page_num}. Sleeping before next page...")
    time.sleep(random.uniform(4, 8))
    print("\nAdzuna scraping complete. Data saved to database.")

def main_adzuna(query, location, pages=1):
    print(f"Starting job scraping for Adzuna: '{query}' in '{location}' for {pages} page(s).")
    scrape_adzuna_jobs(query=query, location=location, pages=pages)
    print("\nAdzuna scraping complete. Data saved to database.")

if __name__ == '__main__':
    init_db()
        
    # Add command line argument parsing with updated defaults
    parser = argparse.ArgumentParser(description='Scrape jobs from Adzuna.')
    parser.add_argument('--query', type=str, default="All", help='Job query terms')
    parser.add_argument('--location', type=str, default="All", help='Job location')
    parser.add_argument('--pages', type=int, default=1, help='Number of pages to scrape')
        
    args = parser.parse_args()
        
    print(f"Preparing to scrape Adzuna for query='{args.query}', location='{args.location}', pages={args.pages}")
    main_adzuna(query=args.query, location=args.location, pages=args.pages)
    print("All scraping finished.")
