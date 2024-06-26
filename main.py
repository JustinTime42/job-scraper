import requests
from bs4 import BeautifulSoup
import re
import csv

visited_urls = []
likely_careers_page = ""
def extract_page_info(url):
    """
    Extracts metadata (like title and description), headings, text,
    finds email addresses on a given website page, and saves it to a CSV file.
    """

    try:
        request_headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=request_headers)
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
    site_map = create_site_map(soup, url, [])

    print(f"site map length: {len(site_map)}")
    for site in site_map:
        print(f"Scraping {site}")
        new_emails = scrape_emails(site)
        for email in new_emails:
            if email not in email_addresses:
                email_addresses.append(email.strip())
        if (site.lower().find("career") != -1) or (site.find("job") != -1) or (site.find("work-with-us") != -1) or (site.find("join-us") != -1):
            print(f"Found careers page: {site}")
            careers_page.append(site)

    # Prepare data for CSV writing
    page_data = [
        {
            "url": url,
            "title": metadata['title'],
            "description": metadata['description'],
            "email_addresses": ",".join(email_addresses) if email_addresses else "",
            "careers_page": ",".join(careers_page) if careers_page else ""
        }
    ]

    # Open or create CSV file
    with open('output.csv', 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["url", "title", "description", "email_addresses", "careers_page"]
        csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header to CSV file
        if csvfile.tell() == 0:  # Check if the file is empty (no headers written)
            csv_writer.writeheader()

        # Append data to CSV file
        for row in page_data:
            csv_writer.writerow(row)

    print(f"Data saved to output.csv")


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

def create_site_map(soup, base_url, site_urls):
    # Get links in the current page
    for link in soup.find_all('a', href=True):
           
        full_link = f"http://{base_url}/{link.get('href')}" if not link.get('href').startswith("http") else link.get('href')
        
        if (get_domain(full_link) == get_domain(base_url)) and (full_link not in visited_urls):
            visited_urls.append(full_link)
            site_urls.append(full_link)
            try:
                response = requests.get(full_link)
                if response.status_code == 200:
                    # Get BeautifulSoup object for the response
                    soup_subpage = BeautifulSoup(response.text, 'html.parser')
                    # Recursively check links within this page
                    for link in soup_subpage.find_all('a', href=True):                        
                        if not link.get('href').startswith("http"):
                            full_link = f"http://{base_url}/{link.get('href')}"
                        else:
                            link.get('href')
                        if get_domain(full_link) == get_domain(base_url):                                    
                            if full_link not in visited_urls:                                    
                                create_site_map(soup_subpage, full_link, site_urls) 
            except Exception as e:
                print(f"Failed to access {full_link}: {str(e)}")
                continue
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
                    emails_found.append(email.strip())                              
    except Exception as e:
        print(f"Failed to access {site}: {str(e)}")
        return []        
    return emails_found

if __name__ == "__main__":
    urls = [
        "https://summitdaymedia.com/",
        "https://www.msialaska.com/",
        "https://wostmann.com/",
        "https://www.7oaksgroup.com/",
        "https://www.flyntlok.com/careers/",
        "https://kartorium.com",
        "https://wostmann.com/",
        "https://queryon.com/",
        "https://nwds-ak.com",
        "https://webbres.com/",
        "https://www.nexusdatasolutions.com/",
        "https://designori.net/",
        "https://www.7oaksgroup.com/",
        "https://grio.com/",
        "https://www.ctg.com",
        "https://www.ripcord.com/",


        
        ]  # Replace with the actual URL
    # extract_page_info(url)
    for url in urls:
        extract_page_info(url)