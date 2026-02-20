"""
Presentation routes - Slideshow viewer for premium plan
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.services.supabase_service import supabase_service
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["presentation"])
templates = Jinja2Templates(directory="src/templates")


@router.get("/p/{presentation_id}", response_class=HTMLResponse)
async def view_presentation(request: Request, presentation_id: str):
    """Render the fullscreen slideshow presentation."""
    presentation = supabase_service.get_presentation(presentation_id)

    if not presentation:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "title": "Apresentacao nao encontrada",
            "message": "Este link nao existe ou expirou.",
        })

    # Increment view count
    supabase_service.increment_view_count(presentation_id)

    slides = presentation.get("slides", [])
    if isinstance(slides, str):
        import json
        slides = json.loads(slides)

    return templates.TemplateResponse("presentation.html", {
        "request": request,
        "presentation": presentation,
        "slides": slides,
    })
