#!/usr/bin/env python3
"""
Script to scrape vehicle detail page (VDP) URLs from a dealership's used inventory page.
Usage: python urlScrape.py <inventory_page_url>
"""
import sys
import re
from pathlib import Path
from typing import List, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# Same constants as scrape_vdp.py for consistency
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT_S = 30


def get_html(url: str) -> str:
    """Fetch HTML content from URL"""
    r = requests.get(url, headers={"User-Agent": UA}, timeout=REQUEST_TIMEOUT_S)
    r.raise_for_status()
    return r.text


def extract_vdp_urls(inventory_url: str) -> Set[str]:
    """
    Extract all vehicle detail page URLs from an inventory listing page.

    Args:
        inventory_url: URL of the inventory listing page (e.g., /used-inventory/index.htm)

    Returns:
        Set of absolute URLs to individual vehicle detail pages
    """
    print(f"[extract_vdp_urls] Fetching inventory page: {inventory_url}", flush=True)
    html = get_html(inventory_url)
    soup = BeautifulSoup(html, "html.parser")

    # Parse the base URL for making absolute URLs
    parsed_base = urlparse(inventory_url)
    base_url = f"{parsed_base.scheme}://{parsed_base.netloc}"

    vdp_urls = set()
    debug_mode = True  # Enable to see all links

    # Find all links on the page
    all_links = soup.find_all("a", href=True)
    print(f"[extract_vdp_urls] Found {len(all_links)} total links on page", flush=True)

    for idx, link in enumerate(all_links):
        href = link["href"]

        # Skip empty hrefs, anchors, and javascript
        if not href or href.startswith("#") or href.startswith("javascript:"):
            continue

        # Convert to absolute URL
        absolute_url = urljoin(inventory_url, href)

        # Show first 10 links for debugging
        if debug_mode and idx < 10:
            print(f"[DEBUG] Link {idx}: {absolute_url}", flush=True)

        # Filter for vehicle detail page patterns
        # Common patterns on dealer.com sites:
        # - /used/Toyota/2020-Toyota-Camry-<vin>-<id>.htm
        # - /certified/Toyota/2020-Toyota-Camry-<vin>-<id>.htm
        # - /vehicle/<vin>
        # - /VehicleDetails/<id>
        # - /inventory/<make>-<model>-<year>-<vin>

        lower_url = absolute_url.lower()

        # CRITICAL: Only get USED or CERTIFIED vehicles, exclude NEW vehicles
        is_new_vehicle = "/new/" in lower_url

        # Check if URL looks like a USED VDP
        is_vdp = any([
            # Dealer.com style USED paths with .htm
            "/used/" in lower_url and ".htm" in lower_url and lower_url != inventory_url.lower(),
            # Certified pre-owned
            "/certified/" in lower_url and ".htm" in lower_url and lower_url != inventory_url.lower(),
            # Generic vehicle paths (but only if not new)
            "/vehicle/" in lower_url and ".htm" in lower_url and not is_new_vehicle,
            "/vehicledetails/" in lower_url and not is_new_vehicle,
        ])

        # Exclude non-VDP pages
        is_excluded = any([
            lower_url == inventory_url.lower(),  # The inventory page itself
            is_new_vehicle,  # Exclude new vehicles
            "/new-inventory/" in lower_url,  # Exclude new inventory listings
            "/search" in lower_url,
            "/contact" in lower_url,
            "/about" in lower_url,
            "/service" in lower_url,
            "/finance" in lower_url,
            "/specials" in lower_url,
            "/hours" in lower_url,
            "/directions" in lower_url,
            "/reviews" in lower_url,
            "/testimonials" in lower_url,
            "toyota.com" in lower_url,  # Exclude external Toyota links
            "youtube.com" in lower_url,
            "facebook.com" in lower_url,
            "instagram.com" in lower_url,
        ])

        if is_vdp and not is_excluded:
            vdp_urls.add(absolute_url)
            print(f"[extract_vdp_urls] Found VDP: {absolute_url}", flush=True)

    print(f"\n[extract_vdp_urls] Total VDP URLs found: {len(vdp_urls)}", flush=True)
    return vdp_urls


def save_urls_to_file(urls: Set[str], output_file: Path):
    """Save URLs to a text file, one per line"""
    with output_file.open("w", encoding="utf-8") as f:
        for url in sorted(urls):
            f.write(f"{url}\n")
    print(f"[save_urls_to_file] Saved {len(urls)} URLs to {output_file}", flush=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python urlScrape.py <inventory_page_url>")
        print("Example: python urlScrape.py https://www.bcstoyota.com/used-inventory/index.htm")
        sys.exit(1)

    inventory_url = sys.argv[1]

    # Extract VDP URLs
    vdp_urls = extract_vdp_urls(inventory_url)

    if not vdp_urls:
        print("\nWARNING: No VDP URLs found on this page.", flush=True)
        print("This could mean:", flush=True)
        print("  - The page structure is different than expected", flush=True)
        print("  - The inventory page has no vehicles listed", flush=True)
        print("  - The URLs don't match the expected patterns", flush=True)
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
