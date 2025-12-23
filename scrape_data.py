import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import time

def get_soup(url):
    """
    Helper to get BeautifulSoup object from URL.
    """
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def find_publication_pages(url, domain_filter=None):
    """
    Finds links to individual publication pages from a listing page.
    """
    soup = get_soup(url)
    if not soup:
        return []
    
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_url = urljoin(url, href)
        
        # Filter to keep only relevant sub-pages
        if domain_filter and domain_filter not in absolute_url:
            continue
            
        # Heuristic: assume publication pages have '/publications/' in URL
        # or are children of the current path
        if '/publications/' in absolute_url and absolute_url != url:
            links.append(absolute_url)
            
    return list(set(links))

def find_document_links(url):
    """
    Scrapes a URL for .pdf or .docx links.
    """
    soup = get_soup(url)
    if not soup:
        return []
        
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.lower().endswith(('.pdf', '.docx')):
            absolute_url = urljoin(url, href)
            links.append(absolute_url)
    
    return list(set(links))

def download_file(url, target_dir):
    """
    Downloads a file from a URL to the target directory.
    """
    try:
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        parsed_url = urlparse(url)
        filename = os.path.basename(unquote(parsed_url.path))
        
        if not filename:
            filename = "downloaded_file"
            
        filepath = os.path.join(target_dir, filename)
        
        if os.path.exists(filepath):
            print(f"File already exists: {filename}")
            return

        print(f"Downloading {url} to {filepath}...")
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded: {filename}")
        
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def main():
    sources = [
        {
            "listing_url": "https://www.crdc.com.au/publications/corporate-publications",
            "domain": "crdc.com.au"
        },
        {
            "listing_url": "https://cottoninfo.com.au/publication-type/manuals-and-guides",
            "domain": "cottoninfo.com.au"
        }
    ]
    
    target_dir = os.path.join("data", "raw")
    
    print(f"Starting scrape job. Target directory: {target_dir}")
    
    all_doc_links = []
    
    for source in sources:
        listing_url = source["listing_url"]
        print(f"\nProcessing listing: {listing_url}")
        
        # 1. Find publication pages
        pub_pages = find_publication_pages(listing_url, source["domain"])
        print(f"Found {len(pub_pages)} publication pages.")
        
        # 2. Scrape each publication page for documents
        for page_url in pub_pages:
            print(f"  Scanning page: {page_url}")
            doc_links = find_document_links(page_url)
            if doc_links:
                print(f"    Found {len(doc_links)} documents.")
                all_doc_links.extend(doc_links)
            else:
                # Fallback: check if the listing page itself had direct links (less likely but possible)
                pass
            time.sleep(0.5) # Be polite
            
    unique_doc_links = list(set(all_doc_links))
    print(f"\nTotal unique documents to download: {len(unique_doc_links)}")
    
    for link in unique_doc_links:
        download_file(link, target_dir)
        
    print("Scraping completed.")

if __name__ == "__main__":
    main()
