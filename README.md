# Premier Impact

**The Silent Guardian of Your Home**

Marketing website for Premier Impact — impact windows, doors, and roofing in South Florida.

## Tech Stack

- **Backend:** Python FastAPI + Jinja2 templates
- **Database:** Supabase (PostgreSQL)
- **Styling:** Vanilla CSS — black, white, red premium design
- **Deployment:** Railway

## Local Development

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your Supabase credentials
uvicorn app.main:app --reload
```

## Pages

- `/` — Home
- `/windows-doors` — Windows & Doors
- `/roofing` — Roofing
- `/contact` — Get a Quote
- `/admin` — View submissions (password protected)
