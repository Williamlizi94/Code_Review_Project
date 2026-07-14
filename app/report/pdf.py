"""PDF report generator using WeasyPrint."""

from loguru import logger

from app.analyzer.base import AnalyzerIssue
from app.report.html import generate_html_report


def generate_pdf_report(
    review_id: str,
    issues: list[AnalyzerIssue],
    summary: str = "",
    target: str | None = None,
    mode: str = "FULL",
) -> bytes | None:
    """Generate a PDF report by converting the HTML report via WeasyPrint.

    Returns PDF bytes, or None if WeasyPrint is not installed.
    """
    try:
        from weasyprint import HTML
    except ImportError:
        logger.warning("WeasyPrint not installed — PDF generation unavailable")
        return None

    html_content = generate_html_report(
        review_id=review_id,
        issues=issues,
        summary=summary,
        target=target,
        mode=mode,
    )

    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}")
        return None
