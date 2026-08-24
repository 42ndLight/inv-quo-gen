from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

# --- Vendor Schemas ---
class VendorBase(BaseModel):
    name: str = Field(..., max_length=255)
    tagline: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)

class VendorCreate(VendorBase):
    pass

class Vendor(VendorBase):
    id: int

    class Config:
        from_attributes = True


# --- Client Schemas ---
class ClientBase(BaseModel):
    name: str = Field(..., max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    attention: Optional[str] = Field(None, max_length=255)

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    id: int

    class Config:
        from_attributes = True


# --- Document Item Schemas ---
class DocumentItemBase(BaseModel):
    item_order: int
    description: str
    unit_label: str = Field(..., max_length=50)
    unit_value: Decimal
    rate: Decimal

class DocumentItemCreate(DocumentItemBase):
    amount: Optional[Decimal] = None

class DocumentItem(DocumentItemBase):
    id: int
    document_id: int
    amount: Decimal

    class Config:
        from_attributes = True


# --- Document Schemas ---
class DocumentBase(BaseModel):
    vendor_id: int
    client_id: int
    doc_type: str
    reference_no: str = Field(..., max_length=100)
    issue_date: str = Field(..., max_length=50)
    currency: str = Field("KSh", max_length=10)
    show_total: str = Field(default="AUTO", max_length=10)

    @field_validator("doc_type")
    @classmethod
    def validate_doc_type(cls, v):
        if v not in ["QUOTATION", "INVOICE"]:
            raise ValueError("doc_type must be either 'QUOTATION' or 'INVOICE'")
        return v

    @field_validator("show_total")
    @classmethod
    def validate_show_total(cls, v):
        if v not in ["AUTO", "YES", "NO"]:
            raise ValueError("show_total must be one of 'AUTO', 'YES', or 'NO'")
        return v

class DocumentCreate(DocumentBase):
    items: List[DocumentItemCreate]

class DocumentUpdate(DocumentBase):
    items: List[DocumentItemCreate]

class Document(DocumentBase):
    id: int
    created_at: datetime
    items: List[DocumentItem]
    vendor: Vendor
    client: Client

    class Config:
        from_attributes = True
