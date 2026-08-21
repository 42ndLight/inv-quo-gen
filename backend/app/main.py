import re
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List

from .database import engine, Base, get_db
from . import models, schemas, pdf_generator

# Ensure all database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EquipHire Quotation & Invoice API")

# Configure CORS so the Vue frontend can make requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to get initials of vendor
def get_vendor_initials(name: str) -> str:
    parts = [p for p in re.split(r'[^a-zA-Z]', name) if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    elif len(parts) == 1:
        return parts[0][:2].upper()
    return "DK"

# Startup event to seed default data if database is empty
@app.on_event("startup")
def seed_data():
    db = next(get_db())
    try:
        # Seed default Vendor
        if db.query(models.Vendor).count() == 0:
            default_vendor = models.Vendor(
                name="Dean.K Plants and Materials",
                tagline="Heavy Equipment Hire - Plant & Machinery",
                location="Juja, Kiambu County",
                phone="+254 716 874 161",
                email="DeanKinyanjuik@gmail.com"
            )
            db.add(default_vendor)
            db.commit()
            print("Seeded default vendor profile.")

        # Seed default Client
        if db.query(models.Client).count() == 0:
            default_client = models.Client(
                name="Ruiru Golf Club",
                location="Ruiru, Kiambu County, Kenya",
                attention="The Club Manager"
            )
            db.add(default_client)
            db.commit()
            print("Seeded default client profile.")
    finally:
        db.close()


@app.get("/api/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# --- VENDORS ---
@app.get("/api/vendors", response_model=List[schemas.Vendor])
def get_vendors(db: Session = Depends(get_db)):
    return db.query(models.Vendor).all()

@app.post("/api/vendors", response_model=schemas.Vendor)
def create_vendor(vendor: schemas.VendorCreate, db: Session = Depends(get_db)):
    db_vendor = models.Vendor(**vendor.dict())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor


# --- CLIENTS ---
@app.get("/api/clients", response_model=List[schemas.Client])
def get_clients(db: Session = Depends(get_db)):
    return db.query(models.Client).all()

@app.post("/api/clients", response_model=schemas.Client)
def create_client(client: schemas.ClientCreate, db: Session = Depends(get_db)):
    db_client = models.Client(**client.dict())
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


# --- DOCUMENTS ---
@app.get("/api/documents", response_model=List[schemas.Document])
def get_documents(db: Session = Depends(get_db)):
    return db.query(models.Document).all()

@app.get("/api/documents/{document_id}", response_model=schemas.Document)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.post("/api/documents", response_model=schemas.Document)
def create_document(doc: schemas.DocumentCreate, db: Session = Depends(get_db)):
    # Verify vendor and client exist
    vendor = db.query(models.Vendor).filter(models.Vendor.id == doc.vendor_id).first()
    client = db.query(models.Client).filter(models.Client.id == doc.client_id).first()
    if not vendor or not client:
        raise HTTPException(status_code=400, detail="Invalid vendor_id or client_id")

    # Business/Validation Rule 2: reference number formatting
    # If not provided, generate automatically
    ref_no = doc.reference_no
    if not ref_no:
        initials = get_vendor_initials(vendor.name)
        type_code = "QUO" if doc.doc_type == "QUOTATION" else "INV"
        year = datetime.now().year
        count = db.query(models.Document).filter(models.Document.doc_type == doc.doc_type).count() + 1
        ref_no = f"{initials}/{type_code}/{year}/{count:03d}"

    # Ensure reference_no is unique
    existing = db.query(models.Document).filter(models.Document.reference_no == ref_no).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Reference number '{ref_no}' already exists")

    # Create Document record
    db_doc = models.Document(
        vendor_id=doc.vendor_id,
        client_id=doc.client_id,
        doc_type=doc.doc_type,
        reference_no=ref_no,
        issue_date=doc.issue_date,
        currency=doc.currency
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Business/Validation Rule 1: Re-verify amount = unit_value * rate
    db_items = []
    for idx, item in enumerate(doc.items):
        calculated_amount = item.unit_value * item.rate
        db_item = models.DocumentItem(
            document_id=db_doc.id,
            item_order=item.item_order or (idx + 1),
            description=item.description,
            unit_label=item.unit_label,
            unit_value=item.unit_value,
            rate=item.rate,
            amount=calculated_amount  # Enforced calculation backend-side
        )
        db_items.append(db_item)
        db.add(db_item)

    db.commit()
    db.refresh(db_doc)
    return db_doc

@app.put("/api/documents/{document_id}", response_model=schemas.Document)
def update_document(document_id: int, doc_payload: schemas.DocumentUpdate, db: Session = Depends(get_db)):
    db_doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Verify vendor and client exist
    vendor = db.query(models.Vendor).filter(models.Vendor.id == doc_payload.vendor_id).first()
    client = db.query(models.Client).filter(models.Client.id == doc_payload.client_id).first()
    if not vendor or not client:
        raise HTTPException(status_code=400, detail="Invalid vendor_id or client_id")

    # Update metadata
    db_doc.vendor_id = doc_payload.vendor_id
    db_doc.client_id = doc_payload.client_id
    db_doc.doc_type = doc_payload.doc_type
    db_doc.reference_no = doc_payload.reference_no
    db_doc.issue_date = doc_payload.issue_date
    db_doc.currency = doc_payload.currency

    # Remove existing items and add updated ones
    db.query(models.DocumentItem).filter(models.DocumentItem.document_id == document_id).delete()

    for idx, item in enumerate(doc_payload.items):
        # Business/Validation Rule 1: Re-verify amount = unit_value * rate
        calculated_amount = item.unit_value * item.rate
        db_item = models.DocumentItem(
            document_id=db_doc.id,
            item_order=item.item_order or (idx + 1),
            description=item.description,
            unit_label=item.unit_label,
            unit_value=item.unit_value,
            rate=item.rate,
            amount=calculated_amount  # Enforced calculation backend-side
        )
        db.add(db_item)

    db.commit()
    db.refresh(db_doc)
    return db_doc

@app.delete("/api/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    db_doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(db_doc)
    db.commit()
    return {"message": "Document successfully deleted"}


# --- CONVERSION LIFECYCLE ---
@app.post("/api/documents/{document_id}/convert", response_model=schemas.Document)
def convert_quotation_to_invoice(document_id: int, db: Session = Depends(get_db)):
    db_doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if db_doc.doc_type != "QUOTATION":
        raise HTTPException(status_code=400, detail="Only documents of type QUOTATION can be converted to INVOICE")

    # Business/Validation Rule 2: Replaces QUO with INV in reference number
    new_reference = db_doc.reference_no.replace("/QUO/", "/INV/")
    
    # Verify new reference_no is unique (if already exists, append count or raise)
    existing = db.query(models.Document).filter(models.Document.reference_no == new_reference).first()
    if existing:
        # If it exists, append current date or small number to keep it unique
        new_reference = f"{new_reference}-CONV"

    # Update document type and reference code
    db_doc.doc_type = "INVOICE"
    db_doc.reference_no = new_reference
    
    db.commit()
    db.refresh(db_doc)
    return db_doc


# --- PDF EXPORT (WEASYPRINT) ---
@app.get("/api/documents/{document_id}/pdf")
def get_document_pdf(document_id: int, db: Session = Depends(get_db)):
    db_doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not db_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Generate the PDF bytes via WeasyPrint
        pdf_bytes = pdf_generator.generate_pdf_bytes(db_doc)
        
        # Clean reference number for filename
        safe_filename = db_doc.reference_no.replace("/", "_")
        
        headers = {
            "Content-Disposition": f'attachment; filename="{safe_filename}.pdf"'
        }
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF Generation Error: {str(e)}")
