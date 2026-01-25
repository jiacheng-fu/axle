#!/usr/bin/env python3
"""
Script to scrape vehicle URLs from dealer.com inventory pages by extracting
vehicle data and constructing URLs.

Usage: python urlScrapeAPI.py <inventory_page_url>
Example: python urlScrapeAPI.py https://www.bcstoyota.com/used-inventory/index.htm
"""
import sys
import json
import re
from pathlib import Path
from typing import Set
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def extract_vdp_urls_from_data(inventory_url: str) -> Set[str]:
    """
    Extract VDP URLs by parsing the page's embedded JSON data or constructing
    URLs from vehicle information.
    """
    print(f"[extract_vdp_urls] Fetching: {inventory_url}", flush=True)

    r = requests.get(inventory_url, headers={"User-Agent": UA}, timeout=30)
    r.raise_for_status()
    html = r.text

    parsed = urlparse(inventory_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    vdp_urls = set()

    # Method 1: Look for JSON data in script tags
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script"):
        if not script.string:
            continue

        # Look for inventory JSON data patterns
        # Common patterns: window.DDC.InvData, inventoryData, etc.

        # Try to find JSON arrays/objects with vehicle data
        json_patterns = [
            r'"inventory"\s*:\s*(\[[\s\S]*?\])',
            r'inventoryData\s*=\s*(\[[\s\S]*?\]);',
            r'window\.DDC\.InvData\s*=\s*({[\s\S]*?});',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, script.string, re.DOTALL)
            for match in matches:
                try:
                    # Try to parse as JSON
                    data = json.loads(match)
                    if isinstance(data, list):
                        vehicles = data
                    elif isinstance(data, dict) and 'inventory' in data:
                        vehicles = data['inventory']
                    else:
                        continue

                    print(f"[extract_vdp_urls] Found {len(vehicles)} vehicles in JSON data", flush=True)

                    # Extract URLs from vehicle data
                    for vehicle in vehicles:
                        if isinstance(vehicle, dict):
                            # Look for link/url field
                            link = vehicle.get('link') or vehicle.get('url') or vehicle.get('href')
                            if link:
                                if link.startswith('http'):
                                    vdp_urls.add(link)
                                else:
                                    vdp_urls.add(f"{base_url}{link}")

                            # Construct URL from vehicle data if no link found
                            elif all(k in vehicle for k in ['year', 'make', 'model']):
                                # Pattern: /used/{Make}/{Year}-{Make}-{Model}-{uuid}.htm
                                year = vehicle.get('year')
                                make = vehicle.get('make', '').replace(' ', '-')
                                model = vehicle.get('model', '').replace(' ', '-')
                                uuid = vehicle.get('uuid') or vehicle.get('id') or vehicle.get('vin', '')

                                if year and make and model and uuid:
                                    url_path = f"/used/{make}/{year}-{make}-{model}-{uuid}.htm"
                                    constructed_url = f"{base_url}{url_path}"
                                    vdp_urls.add(constructed_url)
                                    print(f"[extract_vdp_urls] Constructed: {constructed_url}", flush=True)

                except json.JSONDecodeError:
                    continue

        # Method 2: Look for URL patterns directly in scripts
        if not vdp_urls:
            url_pattern = r'((?:https?:)?//[^\s"\']+/used/[^\s"\']+\.htm)'
            urls = re.findall(url_pattern, script.string)
            for url in urls:
                if url.startswith('//'):
                    url = f"{parsed.scheme}:{url}"
                elif url.startswith('/'):
                    url = f"{base_url}{url}"

                if '/used/' in url and url not in vdp_urls:
                    vdp_urls.add(url)
                    print(f"[extract_vdp_urls] Found URL in script: {url}", flush=True)

    # Method 3: Parse HTML for vehicle cards with data attributes
    if not vdp_urls:
        print("[extract_vdp_urls] No JSON data found, trying HTML parsing...", flush=True)
        vehicle_cards = soup.find_all(['li', 'div'], class_=lambda x: x and 'vehicle-card' in str(x))

        for card in vehicle_cards:
            # Look for data-uuid or similar attributes
            uuid = card.get('data-uuid') or card.get('data-id') or card.get('data-vin')

            # Try to find vehicle info in the card
            year_elem = card.find(class_=lambda x: x and 'year' in str(x).lower())
            make_elem = card.find(class_=lambda x: x and 'make' in str(x).lower())
            model_elem = card.find(class_=lambda x: x and 'model' in str(x).lower())

            # Look for any href links in the card
            links = card.find_all('a', href=True)
            for link in links:
                href = link['href']
                if '/used/' in href and '.htm' in href:
                    if href.startswith('http'):
                        vdp_urls.add(href)
                    elif href.startswith('/'):
                        vdp_urls.add(f"{base_url}{href}")
                    else:
                        vdp_urls.add(f"{base_url}/{href}")

    print(f"\n[extract_vdp_urls] Total VDP URLs found: {len(vdp_urls)}", flush=True)
    return vdp_urls


def save_urls_to_file(urls: Set[str], output_file: Path):
    """Save URLs to text file"""
    with output_file.open("w", encoding="utf-8") as f:
        for url in sorted(urls):
            f.write(f"{url}\n")
    print(f"[save_urls_to_file] Saved {len(urls)} URLs to {output_file}", flush=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python urlScrapeAPI.py <inventory_page_url>")
        print("Example: python urlScrapeAPI.py https://www.bcstoyota.com/used-inventory/index.htm")
        sys.exit(1)

    inventory_url = sys.argv[1]

    vdp_urls = extract_vdp_urls_from_data(inventory_url)

    if not vdp_urls:
        print("\nWARNING: No VDP URLs found.", flush=True)
        print("The inventory page may use JavaScript to load vehicles dynamically.", flush=True)
        print("Try using urlScrapeSelenium.py instead for JavaScript-heavy sites.", flush=True)
        sys.exit(1)

    output_file = Path(__file__).parent / "vdp_urls.txt"
    save_urls_to_file(vdp_urls, output_file)

    print(f"\nSuccessfully extracted {len(vdp_urls)} VDP URLs")
    print(f"URLs saved to: {output_file}")
    print(f"\nYou can now scrape each VDP with:")
    print(f"  Get-Content vdp_urls.txt | ForEach-Object {{ python scrape_vdp.py $_ }}")


if __name__ == "__main__":
    main()
