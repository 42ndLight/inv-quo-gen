import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

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
        total_amount=total_amount
    )
    
    # Convert HTML string to PDF bytes
    pdf_bytes = HTML(string=rendered_html).write_pdf()
    return pdf_bytes
