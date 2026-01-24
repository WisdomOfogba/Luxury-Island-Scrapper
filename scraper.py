import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os

# Your specific Island URLs
LOCATIONS = [
    "https://nigeriapropertycentre.com/for-rent/lagos/ikoyi",
    "https://nigeriapropertycentre.com/for-rent/lagos/victoria-island",
    "https://nigeriapropertycentre.com/for-rent/lagos/ikoyi/banana-island",
    "https://nigeriapropertycentre.com/for-rent/lagos/victoria-island/oniru"
]

STATE_FILE = "state.txt"
PAGES_PER_RUN = 5
CSV_FILE = "Island_Luxury_Data.csv"

def get_last_page():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return 0
    return 0

def save_last_page(page_num):
    with open(STATE_FILE, "w") as f:
        f.write(str(page_num))

def scrape_luxury_zone():
    all_results = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    start_page = get_last_page() + 1
    end_page = start_page + PAGES_PER_RUN

    for base_url in LOCATIONS:
        print(f"--- Starting Scrape for: {base_url} ---")
        
        for page in range(start_page, end_page):
            url = f"{base_url}?page={page}"
            try:
                response = requests.get(url, headers=headers, timeout=15)
                if response.status_code != 200:
                    print(f"Skipping page {page} due to status {response.status_code}")
                    continue
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                # Updated container based on your HTML snippet
                props = soup.find_all('div', class_='wp-block property list') 
                
                if not props:
                    print(f"No properties found on page {page}. Ending location scrape.")
                    break

                for p in props:
                    # 1. Title & URL (from the h3 in wp-block-title)
                    title_tag = p.find('div', class_='wp-block-title').find('h3') if p.find('div', class_='wp-block-title') else None
                    title = title_tag.text.strip() if title_tag else "N/A"
                    
                    url_tag = p.find('div', class_='wp-block-title').find('a') if p.find('div', class_='wp-block-title') else None
                    link = "https://nigeriapropertycentre.com" + url_tag['href'] if url_tag else "N/A"

                    # 2. Location & Description
                    content_div = p.find('div', class_='wp-block-content')
                    location = content_div.find('address').text.strip() if content_div and content_div.find('address') else "N/A"
                    property_type = content_div.find('h4', class_='content-title').text.strip() if content_div and content_div.find('h4', class_='content-title') else "N/A"

                    # 3. Price (Raw text as per project requirements)
                    price_span = content_div.find('span', class_='price') if content_div else None
                    # Note: We take all text in the price span including the currency symbol
                    price = price_span.parent.text.strip() if price_span else "0"

                    # 4. Amenities (Beds, Baths, Toilets) from aux-info list
                    bed, bath, toilet = 0, 0, 0
                    aux_info = p.find('ul', class_='aux-info')
                    if aux_info:
                        for li in aux_info.find_all('li'):
                            txt = li.text.lower()
                            val = li.find('span').text.strip() if li.find('span') else "0"
                            if "bedroom" in txt: bed = val
                            elif "bathroom" in txt: bath = val
                            elif "toilet" in txt: toilet = val

                    all_results.append({
                        'title': title,
                        'location': location,
                        'price': price,
                        'bedrooms': bed,
                        'bathrooms': bath,
                        'toilets': toilet,
                        'property_type': property_type,
                        'url': link
                    })
                
                print(f"Page {page} collected {len(props)} listings.")
                time.sleep(random.uniform(5, 10)) # Safe delay
                
            except Exception as e:
                print(f"Error on {url}: {e}")

    # 5. Load, Merge, and Deduplicate
    df_new = pd.DataFrame(all_results)
    if os.path.exists(CSV_FILE):
        df_old = pd.read_csv(CSV_FILE)
        df_final = pd.concat([df_old, df_new]).drop_duplicates(subset=['url'], keep='first')
    else:
        df_final = df_new

    df_final.to_csv(CSV_FILE, index=False)
    save_last_page(end_page - 1)
    print(f"Total Unique Listings: {len(df_final)}. State updated to page {end_page - 1}.")

if __name__ == "__main__":
    scrape_luxury_zone()