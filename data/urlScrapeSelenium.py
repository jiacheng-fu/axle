#!/usr/bin/env python3
"""
Script to scrape vehicle detail page (VDP) URLs from a dealership's used inventory page.
This version uses Selenium to handle JavaScript-rendered pages.

Usage: python urlScrapeSelenium.py <inventory_page_url>
"""
import sys
import time
from pathlib import Path
from typing import Set
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup


def setup_driver():
    """Setup Chrome driver with headless options"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    return driver


def extract_vdp_urls_selenium(inventory_url: str) -> Set[str]:
    """
    Extract all vehicle detail page URLs from an inventory listing page using Selenium.

    Args:
        inventory_url: URL of the inventory listing page

    Returns:
        Set of absolute URLs to individual vehicle detail pages
    """
    print(f"[extract_vdp_urls_selenium] Fetching inventory page with Selenium: {inventory_url}", flush=True)

    driver = setup_driver()
    vdp_urls = set()

    try:
        # Load the page
        driver.get(inventory_url)

        # Wait for vehicle cards to load (up to 15 seconds)
        print("[extract_vdp_urls_selenium] Waiting for vehicle cards to load...", flush=True)
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "vehicle-card"))
            )
            print("[extract_vdp_urls_selenium] Vehicle cards loaded!", flush=True)
        except Exception as e:
            print(f"[extract_vdp_urls_selenium] Timeout waiting for vehicle cards: {e}", flush=True)

        # Give extra time for JavaScript to populate links
        time.sleep(3)

        # Scroll down to trigger lazy loading
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Get the page source after JavaScript execution
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, "html.parser")

        # Find all vehicle cards
        vehicle_cards = soup.find_all(['li', 'div'], class_=lambda x: x and 'vehicle-card' in str(x))
        print(f"[extract_vdp_urls_selenium] Found {len(vehicle_cards)} vehicle cards", flush=True)

        # Extract links from vehicle cards
        for card in vehicle_cards:
            # Look for links inside the card
            links = card.find_all('a', href=True)
            for link in links:
                href = link['href']

                # Skip empty, anchor, and javascript links
                if not href or href.startswith('#') or href.startswith('javascript:'):
                    continue

                # Convert to absolute URL
                absolute_url = urljoin(inventory_url, href)
                lower_url = absolute_url.lower()

                # Filter for VDP patterns
                is_vdp = any([
                    '/used/' in lower_url and '.htm' in lower_url,
                    '/certified/' in lower_url and '.htm' in lower_url,
                ])

                # Exclude non-VDP URLs
                is_excluded = any([
                    lower_url == inventory_url.lower(),
                    '/new/' in lower_url,
                    '/contact' in lower_url,
                    '/finance' in lower_url,
                    '/service' in lower_url,
                    'facebook.com' in lower_url,
                    'youtube.com' in lower_url,
                    'instagram.com' in lower_url,
                    'toyota.com' in lower_url,
                ])

                if is_vdp and not is_excluded:
                    vdp_urls.add(absolute_url)
                    print(f"[extract_vdp_urls_selenium] Found VDP: {absolute_url}", flush=True)

        # Also try finding links directly in the page
        if not vdp_urls:
            print("[extract_vdp_urls_selenium] No VDPs found in cards, trying direct link search...", flush=True)
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                if not href or href.startswith('#') or href.startswith('javascript:'):
                    continue

                absolute_url = urljoin(inventory_url, href)
                lower_url = absolute_url.lower()

                if (('/used/' in lower_url or '/certified/' in lower_url) and
                    '.htm' in lower_url and
                    '/new/' not in lower_url and
                    lower_url != inventory_url.lower()):
                    vdp_urls.add(absolute_url)
                    print(f"[extract_vdp_urls_selenium] Found VDP: {absolute_url}", flush=True)

    finally:
        driver.quit()

    print(f"\n[extract_vdp_urls_selenium] Total VDP URLs found: {len(vdp_urls)}", flush=True)
    return vdp_urls


def save_urls_to_file(urls: Set[str], output_file: Path):
    """Save URLs to a text file, one per line"""
    with output_file.open("w", encoding="utf-8") as f:
        for url in sorted(urls):
            f.write(f"{url}\n")
    print(f"[save_urls_to_file] Saved {len(urls)} URLs to {output_file}", flush=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python urlScrapeSelenium.py <inventory_page_url>")
        print("Example: python urlScrapeSelenium.py https://www.bcstoyota.com/used-inventory/index.htm")
        sys.exit(1)

    inventory_url = sys.argv[1]

    # Extract VDP URLs using Selenium
    vdp_urls = extract_vdp_urls_selenium(inventory_url)

    if not vdp_urls:
        print("\nWARNING: No VDP URLs found on this page.", flush=True)
        print("This could mean:", flush=True)
        print("  - The page structure is different than expected", flush=True)
        print("  - The inventory page has no vehicles listed", flush=True)
        print("  - The JavaScript didn't load properly", flush=True)
        sys.exit(1)

    # Save to file
    output_file = Path(__file__).parent / "vdp_urls.txt"
    save_urls_to_file(vdp_urls, output_file)

    print(f"\nSuccessfully extracted {len(vdp_urls)} VDP URLs")
    print(f"URLs saved to: {output_file}")
    print(f"\nYou can now scrape each VDP with:")
    print(f"  while read url; do python scrape_vdp.py \"$url\"; done < vdp_urls.txt")


if __name__ == "__main__":
    main()
