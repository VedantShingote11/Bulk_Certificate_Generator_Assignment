import os
import uuid
from pathlib import Path

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from app.core.config import settings

BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / settings.CERTIFICATE_OUTPUT_DIR

# ── Colour palette (light/professional) ──────────────────────────────────────
NAVY        = (0.08, 0.13, 0.30)       # #152051  header bar
NAVY_MID    = (0.11, 0.18, 0.42)       # #1d2e6b  accent text
BLUE        = (0.15, 0.38, 0.92)       # #2663eb  rule lines / accents
BLUE_LIGHT  = (0.91, 0.95, 1.00)       # #e8f2ff  tinted panel
SLATE       = (0.29, 0.36, 0.50)       # #4a5c80  muted text
SILVER      = (0.80, 0.83, 0.90)       # #ccd4e6  light dividers
WHITE       = (1.00, 1.00, 1.00)
OFF_WHITE   = (0.97, 0.98, 0.99)       # #f7f8fc  page background
GOLD        = (0.72, 0.53, 0.04)       # #b78709  seal accent
# ─────────────────────────────────────────────────────────────────────────────


def _rgb(c: canvas.Canvas, triplet: tuple, alpha: float = 1.0) -> None:
    """Set fill colour from an RGB triplet."""
    c.setFillColorRGB(*triplet, alpha=alpha)


def _stroke(c: canvas.Canvas, triplet: tuple, alpha: float = 1.0) -> None:
    c.setStrokeColorRGB(*triplet, alpha=alpha)


def _draw_certificate(
    c: canvas.Canvas,
    W: float,
    H: float,
    recipient_name: str,
    event_name: str,
    course_name: str,
    issued_by: str,
    issue_date: str,
) -> None:

    # ── Page background ──────────────────────────────────────────────────────
    _rgb(c, OFF_WHITE)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── Navy header bar ──────────────────────────────────────────────────────
    header_h = 72
    _rgb(c, NAVY)
    c.rect(0, H - header_h, W, header_h, fill=1, stroke=0)

    # Thin gold rule at very top of header
    _rgb(c, GOLD)
    c.rect(0, H - 4, W, 4, fill=1, stroke=0)

    # Header text — organisation / issuer name (top-right)
    _rgb(c, WHITE, alpha=0.5)
    c.setFont("Helvetica", 8)
    c.drawRightString(W - 28, H - 18, issued_by.upper())

    # Header centred title
    _rgb(c, WHITE)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(W / 2, H - 38, "CERTIFICATE  OF  ACHIEVEMENT")
    _rgb(c, WHITE, alpha=0.55)
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(W / 2, H - 55, event_name.upper())

    # Blue accent line under header
    _rgb(c, BLUE)
    c.rect(0, H - header_h, W, 3, fill=1, stroke=0)

    # ── Blue tinted centre panel ─────────────────────────────────────────────
    panel_top    = H - header_h - 3
    panel_bottom = 110
    panel_h      = panel_top - panel_bottom
    margin_x     = 36

    _rgb(c, BLUE_LIGHT)
    c.roundRect(margin_x, panel_bottom, W - 2 * margin_x, panel_h, 6, fill=1, stroke=0)

    # Thin border around panel
    _stroke(c, BLUE, alpha=0.18)
    c.setLineWidth(0.7)
    c.roundRect(margin_x, panel_bottom, W - 2 * margin_x, panel_h, 6, fill=0, stroke=1)

    # ── "This is to certify that" ────────────────────────────────────────────
    certify_y = H - header_h - 44
    _rgb(c, SLATE)
    c.setFont("Helvetica", 11)
    c.drawCentredString(W / 2, certify_y, "This is to certify that")

    # ── Recipient name ───────────────────────────────────────────────────────
    name_y = certify_y - 40
    name_size = 38 if len(recipient_name) <= 22 else (30 if len(recipient_name) <= 32 else 24)
    _rgb(c, NAVY)
    c.setFont("Helvetica-Bold", name_size)
    c.drawCentredString(W / 2, name_y, recipient_name)

    # Blue underline beneath name
    name_w = c.stringWidth(recipient_name, "Helvetica-Bold", name_size)
    ul_pad = 16
    _rgb(c, BLUE)
    c.rect(W / 2 - name_w / 2 - ul_pad, name_y - 7, name_w + ul_pad * 2, 2.5, fill=1, stroke=0)

    # ── "has successfully completed" ─────────────────────────────────────────
    comp_y = name_y - 34
    _rgb(c, SLATE)
    c.setFont("Helvetica", 11)
    c.drawCentredString(W / 2, comp_y, "has successfully completed")

    # ── Course / programme name ──────────────────────────────────────────────
    display = course_name if course_name else event_name
    prog_size = 20 if len(display) <= 38 else (16 if len(display) <= 55 else 13)
    prog_y = comp_y - 32
    _rgb(c, NAVY_MID)
    c.setFont("Helvetica-Bold", prog_size)
    c.drawCentredString(W / 2, prog_y, display)

    # If course != event, show event as sub-label
    if course_name and course_name.strip().lower() != event_name.strip().lower():
        sub_y = prog_y - 18
        _rgb(c, SLATE)
        c.setFont("Helvetica", 9.5)
        c.drawCentredString(W / 2, sub_y, f"as part of  {event_name}")

    # ── Divider ──────────────────────────────────────────────────────────────
    div_y = panel_bottom + 72
    _rgb(c, SILVER)
    c.rect(margin_x + 24, div_y, W - 2 * margin_x - 48, 0.8, fill=1, stroke=0)

    # ── Bottom signature columns ─────────────────────────────────────────────
    col_l = W * 0.27
    col_r = W * 0.73
    sig_y  = panel_bottom + 46
    sig_label_y = panel_bottom + 24

    for cx in [col_l, col_r]:
        _stroke(c, NAVY, alpha=0.35)
        c.setLineWidth(0.8)
        c.line(cx - 65, sig_y, cx + 65, sig_y)

    _rgb(c, NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(col_l, sig_y - 13, issued_by)
    c.drawCentredString(col_r, sig_y - 13, issue_date)

    _rgb(c, SLATE)
    c.setFont("Helvetica", 8)
    c.drawCentredString(col_l, sig_label_y, "AUTHORISED SIGNATORY")
    c.drawCentredString(col_r, sig_label_y, "DATE OF ISSUE")

    # ── Seal / badge circle (left of bottom) ─────────────────────────────────
    seal_x, seal_y, seal_r = margin_x + 46, panel_bottom + 48, 24
    _rgb(c, NAVY)
    c.circle(seal_x, seal_y, seal_r, fill=1, stroke=0)
    _rgb(c, GOLD)
    c.circle(seal_x, seal_y, seal_r + 3, fill=0, stroke=1)
    c.setLineWidth(1)
    _rgb(c, WHITE)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(seal_x, seal_y + 4, "CERTIFIED")
    c.setFont("Helvetica", 5.5)
    c.drawCentredString(seal_x, seal_y - 4, "ACHIEVEMENT")

    # ── Navy footer strip ─────────────────────────────────────────────────────
    footer_h = 26
    _rgb(c, NAVY)
    c.rect(0, 0, W, footer_h, fill=1, stroke=0)

    # Gold bottom rule
    _rgb(c, GOLD)
    c.rect(0, footer_h, W, 2, fill=1, stroke=0)

    cert_id = str(uuid.uuid4())[:8].upper()
    _rgb(c, WHITE, alpha=0.45)
    c.setFont("Helvetica", 7)
    c.drawCentredString(W / 2, 9, f"Certificate ID: {cert_id}   ·   {event_name}")


def generate_certificate_pdf(
    recipient_name: str,
    event_name: str,
    issued_by: str,
    issue_date: str,
    course_name: str = "",
    output_dir: str = None,
) -> str:
    if output_dir is None:
        abs_output_dir = DEFAULT_OUTPUT_DIR
    else:
        abs_output_dir = Path(output_dir).resolve()

    abs_output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}.pdf"
    filepath = str(abs_output_dir / filename)

    page_width, page_height = landscape(A4)
    c = canvas.Canvas(filepath, pagesize=landscape(A4))
    c.setTitle(f"Certificate — {recipient_name}")

    _draw_certificate(
        c,
        page_width,
        page_height,
        recipient_name=recipient_name,
        event_name=event_name,
        course_name=course_name or "",
        issued_by=issued_by,
        issue_date=issue_date,
    )

    c.save()
    return filepath
