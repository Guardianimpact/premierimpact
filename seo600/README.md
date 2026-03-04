# SEO600 — 600 Location Page Engine

Generates 600 SEO-optimized location pages (200 cities × 3 services) for Premier Impact Windows & Roofing.

## Prerequisites

Add to `.env`:
```
ANTHROPIC_API_KEY=sk-ant-api03-...
SEO600_ENABLED=true
SITE_DOMAIN=premierimpactfl.com
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## CLI Commands

### Generate all 600 pages
```bash
python -m seo600.builder --run
```

### Generate for a specific service
```bash
python -m seo600.builder --run --service impact-windows
python -m seo600.builder --run --service impact-doors
python -m seo600.builder --run --service roofing
```

### Generate for a specific city
```bash
python -m seo600.builder --run --city boca-raton
```

### Resume after interruption
```bash
python -m seo600.builder --run --resume
```

### Check generation status
```bash
python -m seo600.builder --status
```

### Regenerate all (clear checkpoints)
```bash
python -m seo600.builder --run --regenerate
```

### Enable/disable location pages
```bash
python -m seo600.builder --enable
python -m seo600.builder --disable
```

### Generate sitemaps
```bash
python -m seo600.sitemap --generate
```

## File Structure

```
seo600/
├── __init__.py
├── cities.py          — 200 city dicts with metadata
├── generator.py       — Claude API content generation
├── checkpoints.py     — Crash-recovery checkpoint system
├── builder.py         — 10-parallel async runner with CLI
├── router.py          — FastAPI routes for location pages
├── sitemap.py         — XML sitemap generator
└── README.md

app/templates/seo600/
├── location_windows.html
├── location_doors.html
├── location_roofing.html
├── locations_index.html
└── county_index.html

app/static/seo600/
└── location.css

data/seo600/
├── generated/
│   ├── impact-windows/   — 200 JSON files
│   ├── impact-doors/     — 200 JSON files
│   └── roofing/          — 200 JSON files
├── checkpoints.json
├── sitemap_index.xml
├── sitemap_windows.xml
├── sitemap_doors.xml
└── sitemap_roofing.xml
```

## Routes

| Route | Description |
|-------|-------------|
| `/locations` | Index of all service areas |
| `/locations/{county}` | County-specific index |
| `/impact-windows/{city}` | Impact windows page for city |
| `/impact-doors/{city}` | Impact doors page for city |
| `/roofing/{city}` | Roofing page for city |
| `/sitemap.xml` | Sitemap index |
