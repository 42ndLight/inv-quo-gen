// API Service for Quotation and Invoice Generator
// Connects to FastAPI backend, falls back to localStorage if backend is offline or for demo purposes.

const BASE_URL = 'http://localhost:8000/api';

// Helper to determine if we should use local storage fallback
let useLocalStorageFallback = false;

// Mock database in case backend is offline
const getLocalData = (key, defaultVal = []) => {
  const data = localStorage.getItem(key);
  return data ? JSON.parse(data) : defaultVal;
};

const saveLocalData = (key, data) => {
  localStorage.setItem(key, JSON.stringify(data));
};

// Seed initial data if localStorage is empty
const seedInitialData = () => {
  if (getLocalData('vendors').length === 0) {
    saveLocalData('vendors', [
      {
        id: 1,
        name: 'Dean.K Plants and Materials',
        tagline: 'Heavy Equipment Hire - Plant & Machinery',
        location: 'Juja, Kiambu County',
        phone: '+254 716 874 161',
        email: 'DeanKinyanjuik@gmail.com'
      }
    ]);
  }

  if (getLocalData('clients').length === 0) {
    saveLocalData('clients', [
      {
        id: 1,
        name: 'Ruiru Golf Club',
        location: 'Ruiru, Kiambu County, Kenya',
        attention: 'The Club Manager'
      }
    ]);
  }

  if (getLocalData('documents').length === 0) {
    saveLocalData('documents', [
      {
        id: 1,
        vendor_id: 1,
        client_id: 1,
        doc_type: 'QUOTATION',
        reference_no: 'DK/QUO/2026/001',
        issue_date: '21st July 2026',
        currency: 'KSh',
        items: [
          {
            id: 1,
            item_order: 1,
            description: 'Motor Grader',
            unit_label: '10.9 Hours',
            unit_value: 10.9,
            rate: 8500.00,
            amount: 92650.00
          }
        ]
      }
    ]);
  }
};

seedInitialData();

async function request(path, options = {}) {
  if (useLocalStorageFallback) {
    throw new Error('Local storage mode active');
  }

  const url = `${BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `HTTP error! status: ${response.status}`);
  }

  return response;
}

export const api = {
  // Test connection to backend
  async checkHealth() {
    try {
      const res = await fetch(`${BASE_URL}/health`);
      if (res.ok) {
        useLocalStorageFallback = false;
        return true;
      }
    } catch (e) {
      console.warn("FastAPI backend not detected. Defaulting to Offline/Demo LocalStorage mode.");
    }
    useLocalStorageFallback = true;
    return false;
  },

  isOfflineMode() {
    return useLocalStorageFallback;
  },

  setOfflineMode(offline) {
    useLocalStorageFallback = offline;
  },

  // Vendors API
  async getVendors() {
    try {
      const res = await request('/vendors');
      return await res.json();
    } catch (err) {
      console.log('API getVendors failed, using local storage:', err.message);
      return getLocalData('vendors');
    }
  },

  async createVendor(vendor) {
    try {
      const res = await request('/vendors', {
        method: 'POST',
        body: JSON.stringify(vendor)
      });
      return await res.json();
    } catch (err) {
      console.log('API createVendor failed, using local storage:', err.message);
      const vendors = getLocalData('vendors');
      const newVendor = { ...vendor, id: vendors.length ? Math.max(...vendors.map(v => v.id)) + 1 : 1 };
      vendors.push(newVendor);
      saveLocalData('vendors', vendors);
      return newVendor;
    }
  },

  // Clients API
  async getClients() {
    try {
      const res = await request('/clients');
      return await res.json();
    } catch (err) {
      console.log('API getClients failed, using local storage:', err.message);
      return getLocalData('clients');
    }
  },

  async createClient(client) {
    try {
      const res = await request('/clients', {
        method: 'POST',
        body: JSON.stringify(client)
      });
      return await res.json();
    } catch (err) {
      console.log('API createClient failed, using local storage:', err.message);
      const clients = getLocalData('clients');
      const newClient = { ...client, id: clients.length ? Math.max(...clients.map(c => c.id)) + 1 : 1 };
      clients.push(newClient);
      saveLocalData('clients', clients);
      return newClient;
    }
  },

  // Documents API
  async getDocuments() {
    try {
      const res = await request('/documents');
      return await res.json();
    } catch (err) {
      console.log('API getDocuments failed, using local storage:', err.message);
      // Join vendor and client info for local data rendering
      const docs = getLocalData('documents');
      const vendors = getLocalData('vendors');
      const clients = getLocalData('clients');
      return docs.map(doc => ({
        ...doc,
        vendor: vendors.find(v => v.id === doc.vendor_id),
        client: clients.find(c => c.id === doc.client_id)
      }));
    }
  },

  async getDocument(id) {
    try {
      const res = await request(`/documents/${id}`);
      return await res.json();
    } catch (err) {
      console.log(`API getDocument(${id}) failed, using local storage:`, err.message);
      const docs = getLocalData('documents');
      const doc = docs.find(d => d.id === Number(id));
      if (!doc) throw new Error('Document not found');
      
      const vendors = getLocalData('vendors');
      const clients = getLocalData('clients');
      return {
        ...doc,
        vendor: vendors.find(v => v.id === doc.vendor_id),
        client: clients.find(c => c.id === doc.client_id)
      };
    }
  },

  async createDocument(document) {
    try {
      const res = await request('/documents', {
        method: 'POST',
        body: JSON.stringify(document)
      });
      return await res.json();
    } catch (err) {
      console.log('API createDocument failed, using local storage:', err.message);
      const docs = getLocalData('documents');
      
      // Auto-increment sequence number locally
      const vendorInitials = document.vendor_initials || 'DK';
      const year = new Date().getFullYear();
      const seq = docs.filter(d => d.doc_type === document.doc_type).length + 1;
      const padSeq = String(seq).padStart(3, '0');
      const typeCode = document.doc_type === 'QUOTATION' ? 'QUO' : 'INV';
      const referenceNo = `${vendorInitials}/${typeCode}/${year}/${padSeq}`;

      const newDoc = {
        ...document,
        id: docs.length ? Math.max(...docs.map(d => d.id)) + 1 : 1,
        reference_no: document.reference_no || referenceNo,
        created_at: new Date().toISOString()
      };
      
      // Calculate amount for each item
      newDoc.items = (document.items || []).map((item, index) => {
        const amt = Number(item.unit_value || 0) * Number(item.rate || 0);
        return {
          ...item,
          id: index + 1,
          item_order: index + 1,
          amount: amt
        };
      });

      docs.push(newDoc);
      saveLocalData('documents', docs);
      return newDoc;
    }
  },

  async updateDocument(id, document) {
    try {
      const res = await request(`/documents/${id}`, {
        method: 'PUT',
        body: JSON.stringify(document)
      });
      return await res.json();
    } catch (err) {
      console.log(`API updateDocument(${id}) failed, using local storage:`, err.message);
      const docs = getLocalData('documents');
      const idx = docs.findIndex(d => d.id === Number(id));
      if (idx === -1) throw new Error('Document not found');
      
      const updatedDoc = {
        ...docs[idx],
        ...document,
        items: (document.items || docs[idx].items).map((item, index) => {
          const amt = Number(item.unit_value || 0) * Number(item.rate || 0);
          return {
            ...item,
            id: item.id || index + 1,
            item_order: index + 1,
            amount: amt
          };
        })
      };

      docs[idx] = updatedDoc;
      saveLocalData('documents', docs);
      return updatedDoc;
    }
  },

  async deleteDocument(id) {
    try {
      await request(`/documents/${id}`, {
        method: 'DELETE'
      });
      return true;
    } catch (err) {
      console.log(`API deleteDocument(${id}) failed, using local storage:`, err.message);
      const docs = getLocalData('documents');
      const filtered = docs.filter(d => d.id !== Number(id));
      saveLocalData('documents', filtered);
      return true;
    }
  },

  async convertToInvoice(id) {
    try {
      const res = await request(`/documents/${id}/convert`, {
        method: 'POST'
      });
      return await res.json();
    } catch (err) {
      console.log(`API convertToInvoice(${id}) failed, using local storage:`, err.message);
      const docs = getLocalData('documents');
      const idx = docs.findIndex(d => d.id === Number(id));
      if (idx === -1) throw new Error('Document not found');
      
      const quotation = docs[idx];
      if (quotation.doc_type !== 'QUOTATION') {
        throw new Error('Document is already an INVOICE');
      }

      // Convert reference number (QUO -> INV)
      const ref = quotation.reference_no.replace('/QUO/', '/INV/');
      
      const invoice = {
        ...quotation,
        doc_type: 'INVOICE',
        reference_no: ref,
      };

      docs[idx] = invoice;
      saveLocalData('documents', docs);
      return invoice;
    }
  },

  // PDF Export
  async downloadPDF(id, reference_no) {
    try {
      if (useLocalStorageFallback) {
        throw new Error('Local storage mode active');
      }
      const response = await fetch(`${BASE_URL}/documents/${id}/pdf`);
      if (!response.ok) throw new Error('Failed to generate PDF');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${reference_no.replace(/\//g, '_')}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('API downloadPDF failed, running print preview instead:', err.message);
      // If offline, open a print dialog of the document (using custom print style in browser)
      alert("Offline Mode: WeasyPrint PDF server is not active. Opening browser Print Preview instead. You can save as PDF using the browser's printer.");
      window.print();
    }
  }
};
