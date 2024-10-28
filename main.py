import requests
from bs4 import BeautifulSoup
import re
import csv
from urllib.parse import urlparse, urlunparse, urljoin
import concurrent.futures
from collections import deque

visited_urls = set()
likely_careers_page = ""
def extract_page_info(url):
    """
    Extracts metadata (like title and description), headings, text,
    finds email addresses on a given website page, and saves it to a CSV file.
    """

    fixed_url = fix_url(url)
    try:
        request_headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(fixed_url, headers=request_headers)
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch the webpage: {e}")
        return

    if response.status_code != 200:
        print(f"Failed to fetch the webpage with status code: {response.status_code}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')

    metadata = {}
    metadata['title'] = extract_title(soup)
    metadata['description'] = extract_description(soup)
    email_addresses = []
    careers_page = []
    site_map = create_site_map_concurrent(fixed_url)
    print(f"site map length: {len(site_map)}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(scrape_emails, site): site for site in site_map}

        for future in concurrent.futures.as_completed(futures):
            site = futures[future]
            try:
                new_emails = future.result()
                print(f"Scraping {site}")
                for email in new_emails:
                    if email not in email_addresses:
                        email_addresses.append(email)
                if any(keyword in site.lower() for keyword in ["career", "job", "work-with-us", "join-us"]):
                    print(f"Found careers page: {site}")
                    careers_page.append(site)
            except Exception as e:
                print(f"Generated an exception for {site}: {e}")

    # Prepare data for CSV writing
    page_data = [
        {
            "url": fixed_url,
            "title": metadata['title'],
            "description": metadata['description'],
            "email_addresses": ",".join(email_addresses) if email_addresses else "",
            "careers_page": ",".join(careers_page) if careers_page else ""
        }
    ]

    # Open or create CSV file
    with open('Abby.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["url", "title", "description", "email_addresses", "careers_page"]
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header to CSV file
        if csvfile.tell() == 0:  # Check if the file is empty (no headers written)
            csv_writer.writeheader()

        # Append data to CSV file
        for row in page_data:
            csv_writer.writerow(row)

    print(f"Data saved to Abby.csv")

def get_domain(url):
    return urlparse(url).netloc

def fix_url(url):
    # Check if the URL already has a scheme (http or https)
    if not re.match(r'http[s]?://', url):
        url = 'http://' + url

    # Parse the URL
    parsed_url = urlparse(url)
    
    # Ensure the scheme is https and strip out the path, params, query, and fragment
    fixed_url = urlunparse(('https', parsed_url.netloc, '', '', '', ''))
    
    return fixed_url

def extract_title(soup):
    title_tag = soup.find('title')
    return title_tag.text.strip() if title_tag else ""


def extract_description(soup):
    meta_tags = soup.find_all('meta', attrs={'name': 'description'})
    for tag in meta_tags:
        description_attribute = tag.get('content')
        if description_attribute:
            return description_attribute.strip()
    return ""

def get_domain(url):
    return url.split('/')[2]

def extract_emails_from_html(soup):

    # Find all <a> tags with a href attribute that starts with "mailto:"
    email_links = soup.find_all('a', attrs={'href': re.compile("^mailto:")})

    emails = []
    for link in email_links:
        url = link.get('href')

        # Extract the part after 'mailto:' which is your email address
        if url and url.startswith("mailto:"):
            email = url[len("mailto:"):].split('?')[0].strip()
            emails.append(email)

    return emails

def scrape_page(url, base_url, site_urls, max_depth, current_depth, queue):
    try:
        response = requests.get(url)
        if response.status_code != 200:
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            full_link = urljoin(base_url, link.get('href'))
            if get_domain(full_link) == get_domain(base_url) and full_link not in visited_urls:
                visited_urls.add(full_link)
                site_urls.append(full_link)
                if current_depth < max_depth:
                    queue.append((full_link, current_depth + 1))
    except Exception as e:
        print(f"Failed to access {url}: {str(e)}")

def create_site_map_concurrent(base_url, max_depth=3, max_workers=10):
    site_urls = []
    visited_urls.add(base_url)
    queue = deque([(base_url, 0)])

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        while queue:
            url, depth = queue.popleft()
            futures.append(executor.submit(scrape_page, url, base_url, site_urls, max_depth, depth, queue))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Generated an exception: {e}")
    
    return site_urls

def scrape_emails(site):
    emails_found = []
    request_headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }           
    try:
        response = requests.get(site, headers=request_headers)
        if response.status_code == 200:
            soup_subpage = BeautifulSoup(response.text, 'html.parser')
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            new_emails = re.findall(email_pattern, soup_subpage.get_text())
            more_emails = extract_emails_from_html(soup_subpage)
            for email in new_emails + more_emails:
                if email not in emails_found:
                    emails_found.append(email.lower().strip())                              
    except Exception as e:
        print(f"Failed to access {site}: {str(e)}")
        return []        
    return emails_found

# Enter the websites you want to scrape here
if __name__ == "__main__":
    urls = [    
    "https://forefrontcorp.com",
    "https://redrootmarketing.com",
    "https://abmarketinggroup.co",
    ]  
    for url in urls:
        extract_page_info(url)
