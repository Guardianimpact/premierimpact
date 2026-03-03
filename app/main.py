import os
import secrets
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from app.database import get_supabase

load_dotenv()

app = FastAPI(title="Premier Impact", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", secrets.token_hex(32)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "premier2024")


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
        "request": request,
        "page": "contact",
        "success": True,
    })


# --- Admin Routes ---

def require_admin(request: Request):
    if not request.session.get("admin"):
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/admin/login"})


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "page": "admin"})


@app.post("/admin/login")
async def admin_login(request: Request, password: str = Form(...)):
    if password == ADMIN_PASSWORD:
        request.session["admin"] = True
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse("admin_login.html", {
        "request": request,
        "page": "admin",
        "error": "Invalid password",
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    if not request.session.get("admin"):
        return RedirectResponse(url="/admin/login", status_code=303)
    db = get_supabase()
    result = db.table("quotes").select("*").order("created_at", desc=True).execute()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "page": "admin",
        "quotes": result.data,
    })


@app.get("/admin/logout")
async def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
