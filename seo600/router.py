"""FastAPI routes for SEO600 location pages."""

import json
import os
import re

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from seo600.cities import ALL_CITIES, COUNTY_INFO, get_cities_by_county, get_city

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "seo600", "generated")

SERVICE_TEMPLATES = {
    "impact-windows": "seo600/location_windows.html",
    "impact-doors": "seo600/location_doors.html",
    "roofing": "seo600/location_roofing.html",
}


def _check_enabled():
    if os.getenv("SEO600_ENABLED", "false").lower() != "true":
        raise HTTPException(status_code=404, detail="SEO600 pages are disabled")


def _load_content(service_slug: str, city_slug: str) -> dict:
    path = os.path.join(DATA_DIR, service_slug, f"{city_slug}.json")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Content not yet generated")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def _serve_location(request: Request, service_slug: str, city_slug: str):
    _check_enabled()
    city = get_city(city_slug)
    if not city:
        raise HTTPException(status_code=404, detail="City not found")
    content = _load_content(service_slug, city_slug)
    template_name = SERVICE_TEMPLATES[service_slug]
    from app.main import templates
    return templates.TemplateResponse(template_name, {
        "request": request,
        "city": city,
        "content": content,
        "service_slug": service_slug,
        "page": "locations",
    })


# Three explicit routes (Fix Issue 3)
@router.get("/impact-windows/{city_slug}", response_class=HTMLResponse)
async def location_windows(request: Request, city_slug: str):
    return await _serve_location(request, "impact-windows", city_slug)


@router.get("/impact-doors/{city_slug}", response_class=HTMLResponse)
async def location_doors(request: Request, city_slug: str):
    return await _serve_location(request, "impact-doors", city_slug)


@router.get("/roofing/{city_slug}", response_class=HTMLResponse)
async def location_roofing(request: Request, city_slug: str):
    return await _serve_location(request, "roofing", city_slug)


@router.get("/locations", response_class=HTMLResponse)
async def locations_index(request: Request):
    _check_enabled()
    counties = {}
    for slug, info in COUNTY_INFO.items():
        counties[slug] = {
            "name": info["name"],
            "cities": sorted(get_cities_by_county(slug), key=lambda c: c["name"]),
        }
    from app.main import templates
    return templates.TemplateResponse("seo600/locations_index.html", {
        "request": request,
        "counties": counties,
        "page": "locations",
    })


@router.get("/locations/{county_slug}", response_class=HTMLResponse)
async def county_index(request: Request, county_slug: str):
    _check_enabled()
    if county_slug not in COUNTY_INFO:
        raise HTTPException(status_code=404, detail="County not found")
    info = COUNTY_INFO[county_slug]
    cities = sorted(get_cities_by_county(county_slug), key=lambda c: c["name"])
    from app.main import templates
    return templates.TemplateResponse("seo600/county_index.html", {
        "request": request,
        "county_name": info["name"],
        "county_slug": county_slug,
        "cities": cities,
        "page": "locations",
    })
