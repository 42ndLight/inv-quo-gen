# System Architecture

**System Overview**

The architecture follows a three-tier design: Vue 3 Single Page Application (SPA) on the frontend, FastAPI (Python) on the backend, and PostgreSQL for relational persistence.

```
[ Vue.js 3 SPA ]  <--->  [ FastAPI (Python) ]  <--->  [ PostgreSQL DB ]
 (Reactive UI)           (Business Logic)              (Persisted Records)
                                |
                         [ WeasyPrint ]
                         (HTML -> PDF)

```

**Component Breakdown**

1. **Frontend (Vue 3 + Tailwind CSS)**: Handles dynamic input binding, instant client-side calculation preview, and document state management.
2. **Backend (FastAPI)**: Validates document payloads, handles auto-incrementing document references, queries PostgreSQL, and renders Jinja2 templates into PDF files via WeasyPrint.
3. **Database (PostgreSQL)**: Stores vendor profiles, client directories, documents, and individual line items with transactional integrity.
