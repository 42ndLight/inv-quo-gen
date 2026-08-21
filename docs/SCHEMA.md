# Database Schema

```sql
-- Vendor profile for header/footer rendering
CREATE TABLE vendors (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL, -- e.g., "Dean.K Plants and Materials"
    tagline VARCHAR(255),       -- e.g., "Heavy Equipment Hire - Plant & Machinery"
    location VARCHAR(255),      -- e.g., "Juja, Kiambu County"
    phone VARCHAR(50),          -- e.g., "+2547000000invoi"
    email VARCHAR(255)          -- e.g., "Dea@gmail.com"
);

-- Client address book
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL, -- e.g., "Ruiru Golf Club"
    location VARCHAR(255),      -- e.g., "Ruiru, Kiambu County, Kenya"
    attention VARCHAR(255)      -- e.g., "The Club Manager"
);

-- Main Quotation / Invoice metadata
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    vendor_id INT REFERENCES vendors(id),
    client_id INT REFERENCES clients(id),
    doc_type VARCHAR(20) CHECK (doc_type IN ('QUOTATION', 'INVOICE')) NOT NULL,
    reference_no VARCHAR(100) UNIQUE NOT NULL, -- e.g., "Ref: DK/QUO/2026/004"
    issue_date VARCHAR(50) NOT NULL,            -- e.g., "21st July 2026"
    currency VARCHAR(10) DEFAULT 'KSh',         -- Currency identifier
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual billable items
CREATE TABLE document_items (
    id SERIAL PRIMARY KEY,
    document_id INT REFERENCES documents(id) ON DELETE CASCADE,
    item_order INT NOT NULL,
    description TEXT NOT NULL,                  -- e.g., "Motor Grader"
    unit_label VARCHAR(50) NOT NULL,            -- e.g., "10.9 Hours"
    unit_value NUMERIC(10, 2) NOT NULL,         -- e.g., 10.9
    rate NUMERIC(12, 2) NOT NULL,               -- e.g., 8500.00
    amount NUMERIC(12, 2) NOT NULL              -- e.g., 92650.00
);
```
