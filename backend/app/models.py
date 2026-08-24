from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, TIMESTAMP, CheckConstraint, func
from sqlalchemy.orm import relationship
from .database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    tagline = Column(String(255))
    location = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))

    # Relationships
    documents = relationship("Document", back_populates="vendor")

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    attention = Column(String(255))

    # Relationships
    documents = relationship("Document", back_populates="client")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    doc_type = Column(String(20), nullable=False)
    reference_no = Column(String(100), unique=True, nullable=False)
    issue_date = Column(String(50), nullable=False)
    currency = Column(String(10), default="KSh")
    show_total = Column(String(10), default="AUTO")  # AUTO follows doc_type; YES/NO override
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Check constraints
    __table_args__ = (
        CheckConstraint(doc_type.in_(["QUOTATION", "INVOICE"]), name="doc_type_check"),
    )

    # Relationships
    vendor = relationship("Vendor", back_populates="documents")
    client = relationship("Client", back_populates="documents")
    items = relationship("DocumentItem", back_populates="document", cascade="all, delete-orphan", order_by="DocumentItem.item_order")

class DocumentItem(Base):
    __tablename__ = "document_items"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    item_order = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    unit_label = Column(String(50), nullable=False)
    unit_value = Column(Numeric(10, 2), nullable=False)
    rate = Column(Numeric(12, 2), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="items")
