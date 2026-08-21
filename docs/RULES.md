# Business & Validation Rules

1. **Calculation Rules**:
* `amount` must always equal `unit_value * rate`.
* Backend must re-verify all calculations before inserting into PostgreSQL or rendering PDFs to prevent front-end tampering.

2. **Reference Code Formatting**:
* Quotation references must follow the pattern `[VENDOR_INITIALS]/QUO/[YEAR]/[SEQUENCE]` (e.g., `DK/QUO/2026/004`).
* Invoice references replace `QUO` with `INV` (e.g., `DK/INV/2026/004`).

3. **Layout & Print Requirements**:
* Every rendered document must include dual signature sign-off blocks (Vendor Authorised Signatory and Client Authorised Signatory) containing fields for `Name`, `Date`, and `Official Stamp`.
* Footers must repeat vendor contact details (Phone, Email, Location) alongside the document reference number.
