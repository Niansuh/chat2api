from fastapi import Request
from fastapi.responses import HTMLResponse

from app import app, templates


@app.get("/login", response_class=HTMLResponse)
async def login_html(request: Request):
    response = templates.TemplateResponse("login.html", {"request": request})
    return response
