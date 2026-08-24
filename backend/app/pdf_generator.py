import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def _should_show_total(doc_data) -> bool:
    """
    Determine whether to show the total block.
    AUTO: show total only for invoices; YES/NO: explicit override.
    """
    flag = getattr(doc_data, "show_total", "AUTO")
    if flag == "YES":
        return True
    if flag == "NO":
        return False
    return getattr(doc_data, "doc_type", "QUOTATION") == "INVOICE"


def generate_pdf_bytes(doc_data) -> bytes:
    """
    Renders the invoice/quotation HTML template with Jinja2 and
    uses WeasyPrint to compile it into PDF bytes.
    """
    template = env.get_template("invoice.html")

    # Calculate sum of all line items
    total_amount = sum(float(item.amount) for item in doc_data.items)

    # Render HTML string
    rendered_html = template.render(
        doc=doc_data,
        total_amount=total_amount,
        show_total=_should_show_total(doc_data)
    )

    # Convert HTML string to PDF bytes
    pdf_bytes = HTML(string=rendered_html).write_pdf()
    return pdf_bytes


def generate_pdf_bytes_from_html(html: str | bytes) -> bytes:
    """
    Converts a raw HTML document directly to PDF bytes with WeasyPrint.
    """
    if isinstance(html, bytes):
        html = html.decode("utf-8")
    return HTML(string=html).write_pdf()
