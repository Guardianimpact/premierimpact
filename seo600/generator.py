"""Claude API content generation for SEO600 location pages."""

import asyncio
import json
import os
import re

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an expert SEO content writer for Premier Impact Windows & Roofing,
a South Florida home improvement company known as "The Kings of Service." You write unique,
locally-relevant, 1,500+ word content for location-specific service pages.

Your writing style:
- Professional yet approachable, authoritative but not salesy
- Heavy use of local details: neighborhoods, landmarks, storms, building codes
- Naturally incorporate the city name and service throughout (not keyword-stuffed)
- Include specific data points about the area (home values, wind zones, storm history)
- Reference Florida Building Code requirements specific to the area
- Mention insurance benefits and savings specific to the region

Brand details:
- Company: Premier Impact Windows & Roofing
- Tagline: "The Kings of Service"
- Window/Door brands: ESW (Eastern Storm Windows) and CWI
- Roofing brands: CertainTeed (shingles) and West Lake (concrete/clay tile)
- 100% in-house installation, 60+ years combined experience
- Financing from $87/mo, $0 down options
- Licensed & Insured, A+ BBB Rating, 500+ homes completed
- Service area: Palm Beach, Broward, Miami-Dade counties

You MUST return valid JSON only, no markdown code fences."""

SERVICE_DETAILS = {
    "impact-windows": {
        "service_name": "Impact Windows",
        "brands": "ESW (Eastern Storm Windows) and CWI",
        "product_focus": "impact-resistant windows with laminated glass, Low-E coatings, and multi-chamber frames",
    },
    "impact-doors": {
        "service_name": "Impact Doors",
        "brands": "ESW (Eastern Storm Windows) and CWI",
        "product_focus": "impact-resistant entry doors, sliding glass doors, and French doors with multi-point locking systems",
    },
    "roofing": {
        "service_name": "Roofing",
        "brands": "CertainTeed (architectural shingles, Landmark series) and West Lake (concrete and clay tile)",
        "product_focus": "full roof replacements and repairs using hurricane-rated shingle and tile systems",
    },
}


def build_user_prompt(city: dict, service_slug: str) -> str:
    svc = SERVICE_DETAILS[service_slug]
    hvhz_note = "This area IS in the High Velocity Hurricane Zone (HVHZ), requiring the strictest building standards in Florida." if city["hvhz"] else "This area is NOT in the HVHZ but still requires hurricane-rated products per Florida Building Code."

    return f"""Write a unique, SEO-optimized location page for {svc["service_name"]} in {city["name"]}, Florida.

CITY DATA:
- City: {city["name"]}
- County: {city["county"]}
- ZIP Codes: {", ".join(city["zip_codes"])}
- Wind Zone: {city["wind_zone"]}
- HVHZ: {hvhz_note}
- Average Home Value: {city["avg_home_value"]}
- Income Tier: {city["income_tier"]}
- Coastal: {"Yes" if city["coastal"] else "No"} ({city["miles_from_coast"]} miles from coast)
- Neighborhoods: {", ".join(city["neighborhoods"])}
- Landmarks: {", ".join(city["landmarks"])}
- Permit Office: {city["permit_office"]}
- Storm History: {", ".join(city["storms"])}
- Storms Since 1990: {city["storm_count"]}
- Pre-1994 Homes: {int(city["pre_1994"] * 100)}%
- Neighboring Cities: {", ".join(city["neighboring_cities"])}

SERVICE DATA:
- Service: {svc["service_name"]}
- Brands: {svc["brands"]}
- Product Focus: {svc["product_focus"]}

Return a JSON object with these exact keys:
{{
    "meta_title": "SEO title tag, 50-60 chars, format: '{svc['service_name']} in {city['name']}, FL | Premier Impact Windows & Roofing'",
    "meta_description": "SEO meta description, 150-160 chars, compelling with local keywords",
    "h1": "Main H1 heading with city name and service, unique phrasing",
    "intro": "2-3 paragraph intro (300+ words) about why {city['name']} homeowners need {svc['service_name'].lower()}. Reference specific neighborhoods, local conditions, and home values.",
    "section_why": {{
        "h2": "Unique H2 about why choose Premier Impact for this service in this city",
        "body": "3-4 paragraphs (300+ words) about Premier Impact's expertise, in-house installation, local experience in {city['name']}"
    }},
    "section_history": {{
        "h2": "Unique H2 about storm history and protection needs",
        "body": "2-3 paragraphs (200+ words) about storm history affecting {city['name']}, referencing specific hurricanes and damage patterns"
    }},
    "section_code": {{
        "h2": "Unique H2 about building codes and requirements",
        "body": "2-3 paragraphs (200+ words) about Florida Building Code requirements specific to {city['county']}, HVHZ status, wind zone ratings, permit process via {city['permit_office']}"
    }},
    "section_products": {{
        "h2": "Unique H2 about the specific product brands for this service (use brand names: {svc['brands']})",
        "body": "2-3 paragraphs (200+ words) about the specific products installed, their features, ratings, and why they're ideal for {city['name']}"
    }},
    "section_cost": {{
        "h2": "Unique H2 about cost and financing",
        "body": "2-3 paragraphs (200+ words) about typical costs for {city['name']} homes ({city['avg_home_value']} avg value), financing from $87/mo, ROI, and insurance savings"
    }},
    "section_insurance": {{
        "h2": "Unique H2 about insurance benefits",
        "body": "2-3 paragraphs (200+ words) about insurance discounts for {svc['service_name'].lower()} in {city['county']}, common carriers, wind mitigation credits"
    }},
    "faqs": [
        {{"q": "Question 1 about {svc['service_name'].lower()} specific to {city['name']}", "a": "Detailed answer (50-100 words)"}},
        {{"q": "Question 2 about cost/financing", "a": "Detailed answer"}},
        {{"q": "Question 3 about permits/codes in {city['county']}", "a": "Detailed answer"}},
        {{"q": "Question 4 about timeline/process", "a": "Detailed answer"}},
        {{"q": "Question 5 about insurance/ROI", "a": "Detailed answer"}}
    ],
    "cta_headline": "Compelling CTA headline mentioning {city['name']}",
    "cta_body": "1-2 sentence CTA body text encouraging action"
}}"""


def _repair_json(text: str) -> str:
    """Fix common JSON issues from LLM output."""
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text[:-3]
        elif "```" in text:
            text = text[:text.rfind("```")]
        text = text.strip()

    # Remove trailing commas before } or ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # Remove any control characters except \n \r \t
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    return text


async def generate_content(city: dict, service_slug: str, max_retries: int = 3) -> dict:
    """Generate SEO content for a city/service combination using Claude API.

    Retries up to max_retries times on failure with exponential backoff.
    """
    prompt = build_user_prompt(city, service_slug)
    last_error = None

    for attempt in range(max_retries):
        try:
            response = await asyncio.wait_for(
                client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=8192,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                ),
                timeout=180,  # 3 minute timeout per request
            )

            text = response.content[0].text.strip()
            text = _repair_json(text)
            return json.loads(text)

        except json.JSONDecodeError as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise

        except asyncio.TimeoutError:
            last_error = TimeoutError("API call timed out after 180s")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise last_error

        except anthropic.RateLimitError:
            # Always retry rate limits with longer backoff
            wait = 5 * (2 ** attempt)
            await asyncio.sleep(wait)
            last_error = Exception("Rate limited")
            if attempt == max_retries - 1:
                raise
            continue

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            raise
