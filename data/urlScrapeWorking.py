#!/usr/bin/env python3
"""
Working URL scraper that handles JavaScript-rendered inventory pages by
directly calling the dealer's inventory API.

Usage: python urlScrapeWorking.py <inventory_page_url>
"""
import sys
import json
from pathlib import Path
from typing import Set
from urllib.parse import urlparse, urljoin

import requests


UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def extract_site_id_from_url(url: str) -> str:
    """Extract dealer site ID from URL"""
    parsed = urlparse(url)
    hostname = parsed.netloc
    # Extract subdomain (e.g., 'bcstoyota' from 'www.bcstoyota.com')
    parts = hostname.split('.')
    if len(parts) >= 2:
        return parts[0].replace('www', '').strip()
    return hostname.replace('.com', '').replace('www', '').strip()


def get_inventory_from_api(inventory_url: str) -> list:
    """
    Fetch inventory data directly from the dealer's API.
    """
    print(f"[get_inventory_from_api] Fetching inventory for: {inventory_url}", flush=True)

    parsed = urlparse(inventory_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # Extract site ID from URL
    site_id = extract_site_id_from_url(inventory_url)
    print(f"[get_inventory_from_api] Detected site ID: {site_id}", flush=True)

    # Determine if it's used or certified inventory
    is_certified = 'certified' in inventory_url.lower()
    condition = 'CERTIFIED' if is_certified else 'USED'

    # Build API request
    api_url = f"{base_url}/apis/widget/INVENTORY_LISTING_DEFAULT_AUTO_{condition}:inventory-data-bus1/getInventory"

    payload = {
        "facetFilters": [],
        "searchText": "",
        "offset": 0,
        "limit": 100  # Get first 100 vehicles
    }

    headers = {
        "User-Agent": UA,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        print(f"[get_inventory_from_api] Calling API: {api_url}", flush=True)
        resp = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if resp.status_code == 200:
            data = resp.json()

            if 'inventory' in data:
                vehicles = data['inventory']
                print(f"[get_inventory_from_api] Found {len(vehicles)} vehicles via API", flush=True)
                return vehicles
            else:
                print(f"[get_inventory_from_api] No 'inventory' key in response", flush=True)
                print(f"[get_inventory_from_api] Response keys: {list(data.keys())}", flush=True)
        else:
            print(f"[get_inventory_from_api] API returned status {resp.status_code}", flush=True)
            print(f"[get_inventory_from_api] Response: {resp.text[:500]}", flush=True)

    except Exception as e:
        print(f"[get_inventory_from_api] API error: {e}", flush=True)

    return []


def build_vdp_url(vehicle: dict, base_url: str) -> str:
    """
    Build VDP URL from vehicle data.
    Pattern: /used/{Make}/{Year}-{Make}-{Model}-{uuid}.htm
    """
    # Try direct link first
    if 'link' in vehicle and vehicle['link']:
        link = vehicle['link']
        if link.startswith('http'):
            return link
        elif link.startswith('/'):
            return f"{base_url}{link}"
        else:
            return f"{base_url}/{link}"

    # Construct URL from vehicle data
    year = vehicle.get('year')
    make = vehicle.get('make', '').replace(' ', '-')
    model = vehicle.get('model', '').replace(' ', '-')

    # Get UUID/ID
    uuid = vehicle.get('uuid') or vehicle.get('id') or vehicle.get('stockNumber') or vehicle.get('vin', '')

    # Determine if certified or used
    condition = vehicle.get('condition', 'USED').lower()
    if condition == 'certified':
        condition_path = 'certified'
    else:
        condition_path = 'used'

    if year and make and model and uuid:
        url_path = f"/{condition_path}/{make}/{year}-{make}-{model}-{uuid}.htm"
        return f"{base_url}{url_path}"

    return None


def extract_vdp_urls(inventory_url: str) -> Set[str]:
    """Extract VDP URLs from inventory page"""
    parsed = urlparse(inventory_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    vdp_urls = set()

    # Get inventory from API
    vehicles = get_inventory_from_api(inventory_url)

    if vehicles:
        for vehicle in vehicles:
            url = build_vdp_url(vehicle, base_url)
            if url:
                vdp_urls.add(url)
                print(f"[extract_vdp_urls] Built URL: {url}", flush=True)

    return vdp_urls


def save_urls_to_file(urls: Set[str], output_file: Path):
    """Save URLs to text file"""
    with output_file.open("w", encoding="utf-8") as f:
        for url in sorted(urls):
            f.write(f"{url}\n")
    print(f"[save_urls_to_file] Saved {len(urls)} URLs to {output_file}", flush=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python urlScrapeWorking.py <inventory_page_url>")
        print("Example: python urlScrapeWorking.py https://www.bcstoyota.com/used-inventory/index.htm")
        sys.exit(1)

    inventory_url = sys.argv[1]

    vdp_urls = extract_vdp_urls(inventory_url)

    if not vdp_urls:
        print("\nWARNING: No VDP URLs found.", flush=True)
        print("This may be due to:", flush=True)
        print("  - The dealership has no vehicles in inventory", flush=True)
        print("  - The API endpoint changed", flush=True)
        print("  - The site uses a different structure", flush=True)
        sys.exit(1)

    output_file = Path(__file__).parent / "vdp_urls.txt"
    save_urls_to_file(vdp_urls, output_file)

    print(f"\nSuccess! Extracted {len(vdp_urls)} VDP URLs")
    print(f"URLs saved to: {output_file}")
    print(f"\nNext step - scrape each vehicle:")
    print(f"  Get-Content vdp_urls.txt | ForEach-Object {{ python scrape_vdp.py $_ }}")


if __name__ == "__main__":
    main()
