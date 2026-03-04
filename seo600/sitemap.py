"""XML sitemap generator for SEO600 location pages."""

import argparse
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from seo600.cities import ALL_CITIES

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "seo600")
DOMAIN = os.getenv("SITE_DOMAIN", "premierimpactfl.com")

SERVICES = {
    "impact-windows": "sitemap_windows.xml",
    "impact-doors": "sitemap_doors.xml",
    "roofing": "sitemap_roofing.xml",
}


def generate_service_sitemap(service_slug: str, filename: str):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = []
    for city in ALL_CITIES:
        json_path = os.path.join(DATA_DIR, "generated", service_slug, f"{city['slug']}.json")
        if os.path.exists(json_path):
            urls.append(f"  <url>\n    <loc>https://{DOMAIN}/{service_slug}/{city['slug']}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>0.8</priority>\n  </url>")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""

    out_path = os.path.join(DATA_DIR, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(xml)
    print(f"  Generated {filename} ({len(urls)} URLs)")
    return len(urls)


def generate_sitemap_index():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sitemaps = [
        f"  <sitemap>\n    <loc>https://{DOMAIN}/sitemap_windows.xml</loc>\n    <lastmod>{today}</lastmod>\n  </sitemap>",
        f"  <sitemap>\n    <loc>https://{DOMAIN}/sitemap_doors.xml</loc>\n    <lastmod>{today}</lastmod>\n  </sitemap>",
        f"  <sitemap>\n    <loc>https://{DOMAIN}/sitemap_roofing.xml</loc>\n    <lastmod>{today}</lastmod>\n  </sitemap>",
    ]

    # Main site pages
    main_pages = [
        ("", "1.0"),
        ("windows-doors", "0.8"),
        ("roofing", "0.8"),
        ("contact", "0.9"),
        ("locations", "0.7"),
        ("locations/palm-beach", "0.6"),
        ("locations/broward", "0.6"),
        ("locations/miami-dade", "0.6"),
        ("sitemap-html", "0.3"),
        ("privacy", "0.2"),
        ("terms", "0.2"),
        ("optout", "0.2"),
        ("llms.txt", "0.1"),
    ]
    main_urls = []
    for path, priority in main_pages:
        loc = f"https://{DOMAIN}/{path}" if path else f"https://{DOMAIN}/"
        main_urls.append(f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{today}</lastmod>\n    <priority>{priority}</priority>\n  </url>")

    # Write main sitemap
    main_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(main_urls)}
</urlset>"""
    with open(os.path.join(DATA_DIR, "sitemap_main.xml"), "w") as f:
        f.write(main_xml)

    sitemaps.insert(0, f"  <sitemap>\n    <loc>https://{DOMAIN}/sitemap_main.xml</loc>\n    <lastmod>{today}</lastmod>\n  </sitemap>")

    index_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(sitemaps)}
</sitemapindex>"""

    out_path = os.path.join(DATA_DIR, "sitemap_index.xml")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(index_xml)
    print(f"  Generated sitemap_index.xml ({len(sitemaps)} sitemaps)")


def generate_all():
    print("SEO600 Sitemap Generator")
    print("=" * 40)
    total = 0
    for service_slug, filename in SERVICES.items():
        total += generate_service_sitemap(service_slug, filename)
    generate_sitemap_index()
    print(f"\nTotal: {total} location URLs across 3 sitemaps")


def main():
    parser = argparse.ArgumentParser(description="SEO600 Sitemap Generator")
    parser.add_argument("--generate", action="store_true", help="Generate all sitemaps")
    args = parser.parse_args()

    if args.generate:
        generate_all()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
