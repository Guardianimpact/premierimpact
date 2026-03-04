import os
import re
import secrets
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from app.database import get_supabase

load_dotenv()

app = FastAPI(title="Premier Impact Windows & Roofing", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", secrets.token_hex(32)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Custom Jinja2 filter: slugify (Fix Issue 2)
def _slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s_]+", "-", value)
    value = re.sub(r"-+", "-", value)
    return value

templates.env.filters["slugify"] = _slugify

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "premier2024")

# --- SEO600 Router ---
from seo600.router import router as seo600_router
app.include_router(seo600_router)


# --- Page Routes ---

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request, "page": "home"})


@app.get("/windows-doors", response_class=HTMLResponse)
async def windows_doors(request: Request):
    return templates.TemplateResponse("windows_doors.html", {"request": request, "page": "windows-doors"})


@app.get("/roofing", response_class=HTMLResponse)
async def roofing(request: Request):
    return templates.TemplateResponse("roofing.html", {"request": request, "page": "roofing"})


@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/optout", response_class=HTMLResponse)
async def optout(request: Request):
    return templates.TemplateResponse("optout.html", {"request": request})


@app.post("/optout", response_class=HTMLResponse)
async def optout_submit(request: Request, phone: str = Form(...)):
    import re
    digits = re.sub(r"\D", "", phone)
    db = get_supabase()
    result = db.table("leads").select("id, phone").execute()
    matched = [r for r in result.data if re.sub(r"\D", "", r.get("phone", "")) == digits]
    if matched:
        for row in matched:
            db.table("leads").update({"sms_consent": False}).eq("id", row["id"]).execute()
        return templates.TemplateResponse("optout.html", {"request": request, "success": True})
    return templates.TemplateResponse("optout.html", {"request": request, "not_found": True})


@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request, "page": "contact"})


@app.post("/contact", response_class=HTMLResponse)
async def contact_submit(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    email: str = Form(...),
    service: str = Form(...),
    message: str = Form(""),
):
    db = get_supabase()
    db.table("quotes").insert({
        "name": name,
        "phone": phone,
        "email": email,
        "service": service,
        "message": message,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return templates.TemplateResponse("contact.html", {
        "request": request, "page": "contact", "success": True,
    })


# --- Lead Form API ---

@app.post("/api/lead")
async def submit_lead(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(""),
    service_interest: str = Form(...),
    best_time: str = Form(""),
    wants_financing: str = Form(""),
    sms_consent: str = Form(""),
    source_page: str = Form(""),
    utm_source: str = Form(""),
    utm_medium: str = Form(""),
    utm_campaign: str = Form(""),
):
    db = get_supabase()
    db.table("leads").insert({
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "address": address,
        "service_interest": service_interest,
        "best_time": best_time,
        "wants_financing": wants_financing == "on",
        "sms_consent": sms_consent == "on",
        "source_page": source_page,
        "utm_source": utm_source,
        "utm_medium": utm_medium,
        "utm_campaign": utm_campaign,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
    return JSONResponse({"ok": True, "first_name": first_name})


# --- SEO ---

@app.get("/sitemap.xml")
async def sitemap():
    # Serve generated sitemap index if available
    sitemap_path = os.path.join(BASE_DIR, "..", "data", "seo600", "sitemap_index.xml")
    if os.path.exists(sitemap_path):
        with open(sitemap_path, "r") as f:
            return Response(content=f.read(), media_type="application/xml")
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://premierimpactfl.com/</loc><priority>1.0</priority></url>
  <url><loc>https://premierimpactfl.com/windows-doors</loc><priority>0.8</priority></url>
  <url><loc>https://premierimpactfl.com/roofing</loc><priority>0.8</priority></url>
  <url><loc>https://premierimpactfl.com/contact</loc><priority>0.9</priority></url>
</urlset>"""
    return Response(content=xml, media_type="application/xml")


@app.get("/sitemap_windows.xml")
async def sitemap_windows():
    path = os.path.join(BASE_DIR, "..", "data", "seo600", "sitemap_windows.xml")
    if not os.path.exists(path):
        raise HTTPException(status_code=404)
    with open(path, "r") as f:
        return Response(content=f.read(), media_type="application/xml")


@app.get("/sitemap_doors.xml")
async def sitemap_doors():
    path = os.path.join(BASE_DIR, "..", "data", "seo600", "sitemap_doors.xml")
    if not os.path.exists(path):
        raise HTTPException(status_code=404)
    with open(path, "r") as f:
        return Response(content=f.read(), media_type="application/xml")


@app.get("/sitemap_roofing.xml")
async def sitemap_roofing():
    path = os.path.join(BASE_DIR, "..", "data", "seo600", "sitemap_roofing.xml")
    if not os.path.exists(path):
        raise HTTPException(status_code=404)
    with open(path, "r") as f:
        return Response(content=f.read(), media_type="application/xml")


@app.get("/robots.txt")
async def robots():
    domain = os.getenv("SITE_DOMAIN", "premierimpactfl.com")
    txt = f"""User-agent: *
Allow: /
Sitemap: https://{domain}/sitemap.xml

User-agent: GPTBot
Disallow: /

User-agent: ChatGPT-User
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: anthropic-ai
Disallow: /"""
    return Response(content=txt, media_type="text/plain")


# --- Admin ---

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "page": "admin"})


@app.post("/admin/login")
async def admin_login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["admin"] = True
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("admin_login.html", {
        "request": request, "page": "admin", "error": "Invalid password",
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse(url="/admin/login", status_code=303)
    db = get_supabase()
    leads = db.table("leads").select("*").order("created_at", desc=True).execute()
    quotes = db.table("quotes").select("*").order("created_at", desc=True).execute()
    return templates.TemplateResponse("admin.html", {
        "request": request, "page": "admin",
        "leads": leads.data, "quotes": quotes.data,
    })


@app.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
