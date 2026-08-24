<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { api } from '@/services/api'

// View state
const activeTab = ref('dashboard') // dashboard, editor, directories
const isLoading = ref(false)
const isOffline = ref(false)

// Data lists
const documents = ref([])
const vendors = ref([])
const clients = ref([])

// Form state
const currentDoc = ref({
  id: null,
  vendor_id: '',
  client_id: '',
  doc_type: 'QUOTATION',
  reference_no: '',
  issue_date: '',
  currency: 'KSh',
  show_total: 'NO',
  items: [],
  vendor_signatory_name: '',
  vendor_signatory_date: '',
  client_signatory_name: '',
  client_signatory_date: ''
})

// Directory modals / new item forms
const showVendorModal = ref(false)
const newVendor = ref({ name: '', tagline: '', location: '', phone: '', email: '' })

const showClientModal = ref(false)
const newClient = ref({ name: '', location: '', attention: '' })

// Alerts / Toasts
const notification = ref(null)
const showToast = (message, type = 'success') => {
  notification.value = { message, type }
  setTimeout(() => {
    notification.value = null
  }, 4000)
}

// Format date helper
const getFormattedDate = (date = new Date()) => {
  const day = date.getDate()
  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ]
  const month = monthNames[date.getMonth()]
  const year = date.getFullYear()

  let suffix = 'th'
  if (day === 1 || day === 21 || day === 31) suffix = 'st'
  else if (day === 2 || day === 22) suffix = 'nd'
  else if (day === 3 || day === 23) suffix = 'rd'

  return `${day}${suffix} ${month} ${year}`
}

// Extract vendor initials helper
const getVendorInitials = (vendorName) => {
  if (!vendorName) return 'DK'
  const parts = vendorName.split(/[^a-zA-Z]/).filter(Boolean)
  if (parts.length >= 2) {
    // Return first letters of first two main words
    return (parts[0][0] + parts[1][0]).toUpperCase()
  }
  return vendorName.slice(0, 2).toUpperCase()
}

// Fetch all initial data
const fetchData = async () => {
  isLoading.value = true
  isOffline.value = await api.checkHealth() === false

  try {
    vendors.value = await api.getVendors()
    clients.value = await api.getClients()
    documents.value = await api.getDocuments()
  } catch (err) {
    showToast('Failed to load data from API. Local data active.', 'error')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchData()
})

// Auto-fill Reference Number
const generateReferenceNumber = () => {
  if (!currentDoc.value.vendor_id || currentDoc.value.id) return

  const vendor = vendors.value.find(v => v.id === Number(currentDoc.value.vendor_id))
  if (!vendor) return

  const initials = getVendorInitials(vendor.name)
  const typeCode = currentDoc.value.doc_type === 'QUOTATION' ? 'QUO' : 'INV'
  const year = new Date().getFullYear()

  // Find seq number for similar documents
  const seq = documents.value.filter(d => d.doc_type === currentDoc.value.doc_type).length + 1
  const padSeq = String(seq).padStart(3, '0')

  currentDoc.value.reference_no = `${initials}/${typeCode}/${year}/${padSeq}`
}

// Watch doc_type and vendor_id to auto-generate reference number
watch(() => currentDoc.value.doc_type, () => {
  generateReferenceNumber()
})

watch(() => currentDoc.value.vendor_id, () => {
  generateReferenceNumber()
})

// Add line item
const addLineItem = () => {
  currentDoc.value.items.push({
    description: '',
    unit_name: 'Hours',
    unit_value: 1,
    rate: 0,
    amount: 0
  })
}

// Remove line item
const removeLineItem = (index) => {
  currentDoc.value.items.splice(index, 1)
}

// Recalculate individual item amount
const calculateItemAmount = (item) => {
  item.amount = Number(item.unit_value || 0) * Number(item.rate || 0)
}

// Computes subtotal/total of the invoice
const docTotal = computed(() => {
  if (!currentDoc.value.items) return 0
  return currentDoc.value.items.reduce((sum, item) => sum + Number(item.amount || 0), 0)
})

// Determine whether to display the total/amount column based on user selection.
// Invoices always show totals. Quotations have exactly two persisted states:
// show_total === 'YES' -> show total, anything else (including legacy 'AUTO') -> hidden.
const showTotalForCurrentDoc = computed(() => {
  if (currentDoc.value.doc_type === 'INVOICE') return true
  return currentDoc.value.show_total === 'YES'
})

// Helper to decide whether any document (including from dashboard lists)
// should render its total/amount column, based on its persisted show_total value.
const shouldShowTotalForDocument = (doc) => {
  if (doc.doc_type === 'INVOICE') return true
  return doc.show_total === 'YES'
}

// Dashboard Stats
const stats = computed(() => {
  const total = documents.value.length
  const quotations = documents.value.filter(d => d.doc_type === 'QUOTATION').length
  const invoices = documents.value.filter(d => d.doc_type === 'INVOICE').length
  return { total, quotations, invoices }
})

// Selected details for rendering inside print preview
const selectedVendor = computed(() => {
  return vendors.value.find(v => v.id === Number(currentDoc.value.vendor_id)) || null
})

const selectedClient = computed(() => {
  return clients.value.find(c => c.id === Number(currentDoc.value.client_id)) || null
})

// Prepare editor for new document
const initNewDocument = (type = 'QUOTATION') => {
  currentDoc.value = {
    id: null,
    vendor_id: vendors.value.length ? vendors.value[0].id : '',
    client_id: clients.value.length ? clients.value[0].id : '',
    doc_type: type,
    reference_no: '',
    issue_date: getFormattedDate(),
    currency: 'KSh',
    show_total: 'NO',
    items: [
      { description: 'Motor Grader', unit_name: 'Hours', unit_value: 10, rate: 8500.00, amount: 92650.00 }
    ],
    vendor_signatory_name: '',
    vendor_signatory_date: getFormattedDate(),
    client_signatory_name: '',
    client_signatory_date: getFormattedDate()
  }
  generateReferenceNumber()
  activeTab.value = 'editor'
}

// Load document into editor
const editDocument = (doc) => {
  currentDoc.value = {
    ...doc,
    show_total: doc.show_total === 'YES' ? 'YES' : 'NO',
    items: doc.items.map(item => {
      // parse unit_value and unit_name from unit_label e.g. "10.9 Hours"
      let unit_name = 'Hours'
      if (item.unit_label) {
        const parts = item.unit_label.split(' ')
        if (parts.length > 1) {
          unit_name = parts.slice(1).join(' ')
        }
      }
      return {
        ...item,
        unit_name
      }
    })
  }
  activeTab.value = 'editor'
}

// Save document to backend
const saveDocument = async () => {
  if (!currentDoc.value.vendor_id || !currentDoc.value.client_id || !currentDoc.value.reference_no) {
    showToast('Please fill in Vendor, Client, and Reference Number.', 'error')
    return
  }

  if (currentDoc.value.items.length === 0) {
    showToast('Please add at least one line item.', 'error')
    return
  }

  // Map items to backend schema format (combining unit_value and unit_name into unit_label)
  const docPayload = {
    vendor_id: Number(currentDoc.value.vendor_id),
    client_id: Number(currentDoc.value.client_id),
    doc_type: currentDoc.value.doc_type,
    reference_no: currentDoc.value.reference_no,
    issue_date: currentDoc.value.issue_date,
    currency: currentDoc.value.currency,
    show_total: currentDoc.value.doc_type === 'INVOICE' ? 'AUTO' : (currentDoc.value.show_total === 'YES' ? 'YES' : 'NO'),
    items: currentDoc.value.items.map((item, index) => ({
      item_order: index + 1,
      description: item.description,
      unit_label: `${item.unit_value} ${item.unit_name}`,
      unit_value: Number(item.unit_value),
      rate: Number(item.rate),
      amount: Number(item.unit_value) * Number(item.rate)
    }))
  }

  isLoading.value = true
  try {
    if (currentDoc.value.id) {
      await api.updateDocument(currentDoc.value.id, docPayload)
      showToast('Document updated successfully!')
    } else {
      await api.createDocument(docPayload)
      showToast('Document created successfully!')
    }
    await fetchData()
    activeTab.value = 'dashboard'
  } catch (err) {
    showToast(`Error saving document: ${err.message}`, 'error')
  } finally {
    isLoading.value = false
  }
}

// Delete Document
const deleteDoc = async (id) => {
  if (!confirm('Are you sure you want to delete this document?')) return

  isLoading.value = true
  try {
    await api.deleteDocument(id)
    showToast('Document deleted successfully.')
    await fetchData()
  } catch (err) {
    showToast('Failed to delete document.', 'error')
  } finally {
    isLoading.value = false
  }
}

// One-click conversion of Quotation to Invoice
const convertToInvoice = async (id) => {
  isLoading.value = true
  try {
    await api.convertToInvoice(id)
    showToast('Quotation successfully converted to Invoice!')
    await fetchData()
  } catch (err) {
    showToast(`Conversion failed: ${err.message}`, 'error')
  } finally {
    isLoading.value = false
  }
}

// Download PDF file (uses saved show_total preference)
const downloadPDF = async (doc) => {
  isLoading.value = true
  try {
    await api.downloadPDF(doc.id, doc.reference_no)
  } catch (err) {
    showToast('Could not download PDF. Using browser print fallback.', 'error')
  } finally {
    isLoading.value = false
  }
}

// Create new vendor profile
const createVendor = async () => {
  if (!newVendor.value.name) return
  try {
    const created = await api.createVendor(newVendor.value)
    vendors.value.push(created)
    currentDoc.value.vendor_id = created.id
    newVendor.value = { name: '', tagline: '', location: '', phone: '', email: '' }
    showVendorModal.value = false
    showToast('Vendor profile added.')
  } catch (err) {
    showToast('Failed to create vendor.', 'error')
  }
}

// Create new client profile
const createClient = async () => {
  if (!newClient.value.name) return
  try {
    const created = await api.createClient(newClient.value)
    clients.value.push(created)
    currentDoc.value.client_id = created.id
    newClient.value = { name: '', location: '', attention: '' }
    showClientModal.value = false
    showToast('Client profile added.')
  } catch (err) {
    showToast('Failed to create client.', 'error')
  }
}

// Calculate Total for specific document list items
const getDocTotalAmount = (doc) => {
  if (!doc.items) return 0
  return doc.items.reduce((sum, item) => sum + Number(item.amount), 0)
}
</script>

<template>
  <div>
    <!-- Toast Notification -->
    <div v-if="notification" :class="[
      'fixed bottom-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white font-medium flex items-center space-x-2 transition-all duration-300',
      notification.type === 'error' ? 'bg-rose-600' : 'bg-emerald-600'
    ]">
      <span>{{ notification.message }}</span>
    </div>

    <!-- API Status Bar (Hidden in Print) -->
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 shadow-sm print:hidden">
      <div class="flex items-center space-x-3">
        <span class="flex h-3 w-3 relative">
          <span :class="['animate-ping absolute inline-flex h-full w-full rounded-full opacity-75', isOffline ? 'bg-amber-400' : 'bg-emerald-400']"></span>
          <span :class="['relative inline-flex rounded-full h-3 w-3', isOffline ? 'bg-amber-500' : 'bg-emerald-500']"></span>
        </span>
        <span class="text-sm font-medium text-slate-700">
          Status: {{ isOffline ? 'Offline/Demo Mode (LocalStorage)' : 'API Connected (PostgreSQL)' }}
        </span>
      </div>

      <div class="flex items-center space-x-2">
        <button
          @click="initNewDocument('QUOTATION')"
          class="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-white bg-indigo-600 rounded-lg shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600 transition"
        >
          + New Quotation
        </button>
        <button
          @click="initNewDocument('INVOICE')"
          class="inline-flex items-center justify-center px-4 py-2 text-sm font-semibold text-indigo-700 bg-indigo-50 rounded-lg shadow-sm hover:bg-indigo-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-600 transition"
        >
          + New Invoice
        </button>
      </div>
    </div>

    <!-- Navigation Tabs (Hidden in Print) -->
    <div class="mb-6 border-b border-slate-200 print:hidden">
      <nav class="flex space-x-8" aria-label="Tabs">
        <button
          @click="activeTab = 'dashboard'"
          :class="[
            activeTab === 'dashboard' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300',
            'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition duration-150'
          ]"
        >
          Document Dashboard
        </button>
        <button
          @click="activeTab = 'editor'"
          :class="[
            activeTab === 'editor' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300',
            'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition duration-150'
          ]"
        >
          Document Editor & Live Preview
        </button>
        <button
          @click="activeTab = 'directories'"
          :class="[
            activeTab === 'directories' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300',
            'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition duration-150'
          ]"
        >
          Vendor & Client Directory
        </button>
      </nav>
    </div>

    <!-- TAB 1: DASHBOARD -->
    <div v-if="activeTab === 'dashboard'" class="space-y-6 print:hidden">
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <div class="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5">
          <div class="text-xs font-semibold text-slate-500 uppercase tracking-wide">Total Generated Documents</div>
          <div class="mt-2 text-3xl font-extrabold text-slate-900">{{ stats.total }}</div>
        </div>
        <div class="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5">
          <div class="text-xs font-semibold text-indigo-500 uppercase tracking-wide">Quotations</div>
          <div class="mt-2 text-3xl font-extrabold text-slate-900">{{ stats.quotations }}</div>
        </div>
        <div class="bg-white overflow-hidden shadow-sm rounded-xl border border-slate-200 p-5">
          <div class="text-xs font-semibold text-emerald-500 uppercase tracking-wide">Invoices</div>
          <div class="mt-2 text-3xl font-extrabold text-slate-900">{{ stats.invoices }}</div>
        </div>
      </div>

      <!-- Document List Table -->
      <div class="bg-white shadow-sm rounded-xl border border-slate-200 overflow-hidden">
        <div class="p-5 border-b border-slate-100 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-slate-900">Stored Documents</h3>
          <button @click="fetchData" class="text-sm font-medium text-indigo-600 hover:text-indigo-500">
            Refresh List
          </button>
        </div>

        <div v-if="isLoading" class="p-12 text-center text-slate-500 font-medium">
          Loading documents...
        </div>

        <div v-else-if="documents.length === 0" class="p-12 text-center text-slate-500">
          No documents found. Click <span class="font-semibold text-indigo-600">New Quotation</span> above to create one.
        </div>

        <div v-else class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-200">
            <thead class="bg-slate-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Ref No.</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Type</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Client</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Issue Date</th>
                <th class="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Value</th>
                <th class="px-6 py-3 class text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-slate-100">
              <tr v-for="doc in documents" :key="doc.id" class="hover:bg-slate-50/50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-900">
                  {{ doc.reference_no }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span :class="[
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold',
                    doc.doc_type === 'QUOTATION' ? 'bg-indigo-50 text-indigo-700 border border-indigo-200' : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  ]">
                    {{ doc.doc_type }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                  <div class="font-medium text-slate-900">{{ doc.client?.name || 'Unknown Client' }}</div>
                  <div class="text-xs text-slate-400">Attn: {{ doc.client?.attention }}</div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                  {{ doc.issue_date }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm font-bold text-slate-900">
                  {{ doc.currency }} {{ getDocTotalAmount(doc).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  <button @click="editDocument(doc)" class="text-indigo-600 hover:text-indigo-900">Edit</button>

                  <button
                    v-if="doc.doc_type === 'QUOTATION'"
                    @click="convertToInvoice(doc.id)"
                    class="text-emerald-600 hover:text-emerald-900"
                    title="Convert Quotation to Invoice"
                  >
                    Convert to Invoice
                  </button>

                  <button @click="downloadPDF(doc)" class="text-amber-600 hover:text-amber-900">
                    PDF
                  </button>

                  <button @click="deleteDoc(doc.id)" class="text-rose-600 hover:text-rose-900">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- TAB 2: EDITOR & PREVIEW -->
    <div v-if="activeTab === 'editor'" class="grid grid-cols-1 lg:grid-cols-12 gap-8">

      <!-- Editor Form (Hidden in Print) -->
      <div class="lg:col-span-5 bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-6 print:hidden">
        <h3 class="text-lg font-bold text-slate-900 border-b border-slate-100 pb-3 flex items-center justify-between">
          <span>Document Configuration</span>
          <span class="text-xs font-normal text-slate-400">Values update preview live</span>
        </h3>

        <!-- Form fields -->
        <div class="space-y-4">
          <!-- Document Type & Currency -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Doc Type</label>
              <select
                v-model="currentDoc.doc_type"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="QUOTATION">Quotation</option>
                <option value="INVOICE">Invoice</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Currency</label>
              <input
                type="text"
                v-model="currentDoc.currency"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <!-- Document Reference & Date -->
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Ref Number</label>
              <input
                type="text"
                v-model="currentDoc.reference_no"
                placeholder="e.g. DK/QUO/2026/004"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-bold"
              />
            </div>
            <div>
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Issue Date</label>
              <input
                type="text"
                v-model="currentDoc.issue_date"
                class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <!-- Vendor Selection -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide">Vendor Header</label>
              <button @click="showVendorModal = true" class="text-xs text-indigo-600 hover:text-indigo-500 font-medium">
                + Create Vendor
              </button>
            </div>
            <select
              v-model="currentDoc.vendor_id"
              class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option v-for="vendor in vendors" :key="vendor.id" :value="vendor.id">
                {{ vendor.name }}
              </option>
            </select>
          </div>

          <!-- Client Selection -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide">Client attention</label>
              <button @click="showClientModal = true" class="text-xs text-indigo-600 hover:text-indigo-500 font-medium">
                + Create Client
              </button>
            </div>
            <select
              v-model="currentDoc.client_id"
              class="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option v-for="client in clients" :key="client.id" :value="client.id">
                {{ client.name }} (Attn: {{ client.attention }})
              </option>
            </select>
          </div>

          <!-- Line Items Section -->
          <div>
            <div class="flex items-center justify-between mb-2">
              <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide">Line Items</label>
              <button
                @click="addLineItem"
                class="inline-flex items-center text-xs text-indigo-600 hover:text-indigo-500 font-medium"
              >
                + Add Item
              </button>
            </div>

            <div class="space-y-3">
              <div v-for="(item, idx) in currentDoc.items" :key="idx" class="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2 relative">
                <!-- Close Button -->
                <button
                  @click="removeLineItem(idx)"
                  class="absolute top-2 right-2 text-slate-400 hover:text-rose-600"
                  title="Remove item"
                >
                  <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>

                <div>
                  <input
                    type="text"
                    v-model="item.description"
                    placeholder="Item description (e.g. Motor Grader)"
                    class="w-full bg-white border border-slate-300 rounded px-2 py-1 text-sm focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div class="grid grid-cols-3 gap-2">
                  <div>
                    <span class="block text-[10px] text-slate-400">Qty / Value</span>
                    <input
                      type="number"
                      step="0.01"
                      v-model="item.unit_value"
                      @input="calculateItemAmount(item)"
                      class="w-full bg-white border border-slate-300 rounded px-2 py-1 text-sm focus:ring-1 focus:ring-indigo-500 font-medium"
                    />
                  </div>
                  <div>
                    <span class="block text-[10px] text-slate-400">Unit Type</span>
                    <input
                      type="text"
                      v-model="item.unit_name"
                      placeholder="Hours"
                      class="w-full bg-white border border-slate-300 rounded px-2 py-1 text-sm focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <span class="block text-[10px] text-slate-400">Rate</span>
                    <input
                      type="number"
                      v-model="item.rate"
                      @input="calculateItemAmount(item)"
                      class="w-full bg-white border border-slate-300 rounded px-2 py-1 text-sm focus:ring-1 focus:ring-indigo-500 font-medium"
                    />
                  </div>
                </div>

                <div v-if="showTotalForCurrentDoc" class="text-right text-xs font-bold text-slate-700">
                  Amount: {{ currentDoc.currency }} {{ (item.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}
                </div>
              </div>
            </div>
          </div>

          <!-- Quotation total display option -->
          <div v-if="currentDoc.doc_type === 'QUOTATION'" class="border-t border-slate-100 pt-3 space-y-3">
            <label class="block text-xs font-semibold text-slate-500 uppercase tracking-wide">Total Amount Display</label>
            <div class="flex items-center space-x-6">
              <label class="inline-flex items-center space-x-2 text-sm text-slate-700 cursor-pointer">
                <input type="radio" value="NO" v-model="currentDoc.show_total" class="text-indigo-600 focus:ring-indigo-500" />
                <span>Hide total</span>
              </label>
              <label class="inline-flex items-center space-x-2 text-sm text-slate-700 cursor-pointer">
                <input type="radio" value="YES" v-model="currentDoc.show_total" class="text-indigo-600 focus:ring-indigo-500" />
                <span>Show total</span>
              </label>
            </div>
          </div>

          <!-- Signatory Names -->
          <div class="border-t border-slate-100 pt-3 space-y-4">
            <h4 class="text-xs font-bold text-slate-900 uppercase">Authorised Signatories</h4>

            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-[10px] font-semibold text-slate-500 uppercase">Vendor Signatory</label>
                <input
                  type="text"
                  v-model="currentDoc.vendor_signatory_name"
                  class="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                />
              </div>
              <div>
                <label class="block text-[10px] font-semibold text-slate-500 uppercase">Client Signatory</label>
                <input
                  type="text"
                  v-model="currentDoc.client_signatory_name"
                  class="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                />
              </div>
            </div>
          </div>
        </div>

        <div class="border-t border-slate-100 pt-4 flex space-x-3">
          <button
            @click="saveDocument"
            class="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-semibold rounded-lg shadow-sm text-white bg-indigo-600 hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            Save Document
          </button>
          <button
            @click="window.print()"
            class="inline-flex justify-center items-center px-4 py-2 border border-slate-300 text-sm font-semibold rounded-lg text-slate-700 bg-white hover:bg-slate-50"
          >
            Print
          </button>
        </div>
      </div>

      <!-- Live Printable Preview Container -->
      <div class="lg:col-span-7 bg-white border border-slate-200 rounded-xl p-8 shadow-sm flex flex-col justify-between print:border-none print:shadow-none print:p-0 min-h-[29.7cm] w-full max-w-[21cm] mx-auto text-[13px] leading-relaxed">

        <!-- TOP BRANDING & DETAILS -->
        <div>
          <div class="flex justify-between items-start border-b-2 border-slate-200 pb-5 mb-6">
            <div>
              <h1 class="text-xl font-bold uppercase text-slate-900 tracking-wide">
                {{ selectedVendor?.name || 'Plants and Materials' }}
              </h1>
              <p class="text-indigo-600 font-bold text-xs uppercase tracking-wider mb-2">
                {{ selectedVendor?.tagline || 'Heavy Equipment Hire - Plant & Machinery' }}
              </p>
              <div class="text-xs text-slate-500 space-y-0.5">
                <p>Location: {{ selectedVendor?.location || 'Kenya' }}</p>
                <p>Phone: {{ selectedVendor?.phone || '+254 700 000 000' }}</p>
                <p>Email: {{ selectedVendor?.email || 'user@email.com' }}</p>
              </div>
            </div>

            <div class="text-right">
              <h2 :class="[
                'text-lg font-black uppercase tracking-widest px-4 py-1.5 rounded-lg border inline-block mb-3',
                currentDoc.doc_type === 'QUOTATION' ? 'text-indigo-700 border-indigo-200 bg-indigo-50/50' : 'text-emerald-700 border-emerald-200 bg-emerald-50/50'
              ]">
                {{ currentDoc.doc_type }}
              </h2>
              <div class="text-xs space-y-1">
                <p><span class="font-bold text-slate-500 uppercase text-[10px]">Reference:</span> <span class="font-bold text-slate-900">{{ currentDoc.reference_no || 'Pending...' }}</span></p>
                <p><span class="font-bold text-slate-500 uppercase text-[10px]">Date:</span> {{ currentDoc.issue_date || 'August 2026' }}</p>
              </div>
            </div>
          </div>

          <!-- CLIENT INFORMATION -->
          <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 mb-6">
            <h3 class="text-slate-400 font-black uppercase text-[10px] tracking-wider mb-2">CLIENT DETAILS</h3>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <p class="text-xs text-slate-500 uppercase">Attention:</p>
                <p class="font-bold text-slate-900 text-sm">{{ selectedClient?.attention || 'The Club Manager' }}</p>
                <p class="font-bold text-slate-900 text-sm mt-1">{{ selectedClient?.name || 'Golf Club' }}</p>
              </div>
              <div class="text-right">
                <p class="text-xs text-slate-500 uppercase">Location:</p>
                <p class="font-medium text-slate-800 text-sm">{{ selectedClient?.location || 'Kenya' }}</p>
              </div>
            </div>
          </div>

          <!-- BILLABLE ITEMS TABLE -->
          <table class="min-w-full divide-y divide-slate-300 border border-slate-200 rounded-xl overflow-hidden mb-6">
            <thead class="bg-slate-100">
              <tr>
                <th class="px-4 py-2 text-left text-xs font-bold text-slate-600 uppercase tracking-wider w-12">#</th>
                <th class="px-4 py-2 text-left text-xs font-bold text-slate-600 uppercase tracking-wider">Description</th>
                <th class="px-4 py-2 text-center text-xs font-bold text-slate-600 uppercase tracking-wider w-28">Quantity</th>
                <th class="px-4 py-2 text-right text-xs font-bold text-slate-600 uppercase tracking-wider w-32">Rate ({{ currentDoc.currency }})</th>
                <th v-if="showTotalForCurrentDoc" class="px-4 py-2 text-right text-xs font-bold text-slate-600 uppercase tracking-wider w-36">Amount ({{ currentDoc.currency }})</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-200 bg-white">
              <tr v-for="(item, idx) in currentDoc.items" :key="idx">
                <td class="px-4 py-2.5 text-slate-500">{{ idx + 1 }}</td>
                <td class="px-4 py-2.5 font-semibold text-slate-900">{{ item.description || 'Description pending...' }}</td>
                <td class="px-4 py-2.5 text-center text-slate-700 font-medium">{{ item.unit_value }} {{ item.unit_name }}</td>
                <td class="px-4 py-2.5 text-right font-medium text-slate-700">{{ Number(item.rate || 0).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</td>
                <td v-if="showTotalForCurrentDoc" class="px-4 py-2.5 text-right font-bold text-slate-900">{{ Number(item.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</td>
              </tr>
              <!-- Empty state fallback inside table -->
              <tr v-if="currentDoc.items.length === 0">
                <td :colspan="showTotalForCurrentDoc ? 5 : 4" class="px-4 py-8 text-center text-slate-400 italic">No line items added yet.</td>
              </tr>
            </tbody>
          </table>

          <!-- TOTAL CALCULATION BLOCK -->
          <div v-if="showTotalForCurrentDoc" class="flex justify-end mb-10">
            <div class="w-72 bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2">
              <div class="flex justify-between items-center text-xs text-slate-500">
                <span>Subtotal:</span>
                <span class="font-medium text-slate-800">{{ currentDoc.currency }} {{ docTotal.toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</span>
              </div>
              <div class="flex justify-between items-center border-t border-slate-200 pt-2 text-sm font-bold text-slate-900">
                <span>Total Due:</span>
                <span class="text-base text-indigo-700">{{ currentDoc.currency }} {{ docTotal.toLocaleString(undefined, { minimumFractionDigits: 2 }) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- DUAL SIGNATURE SIGN-OFF BLOCKS -->
        <div>
          <div class="grid grid-cols-2 gap-8 border-t border-slate-200 pt-8 mb-8">
            <!-- Vendor authorized sign-off -->
            <div class="space-y-4">
              <h4 class="font-bold text-xs uppercase text-slate-500 tracking-wider">Vendor Authorised Signatory</h4>
              <div class="border-b border-dashed border-slate-300 h-10 flex items-end">
                <span class="text-xs text-slate-400 italic">Sign / Stamp Here</span>
              </div>
              <div class="text-xs space-y-1 text-slate-600">
                <p><span class="font-semibold text-slate-400">Name:</span> {{ currentDoc.vendor_signatory_name || '_____________________' }}</p>
                <p><span class="font-semibold text-slate-400">Date:</span> {{ currentDoc.vendor_signatory_date || '_____________________' }}</p>
                <p><span class="font-semibold text-slate-400">Official Stamp:</span> _____________________</p>
              </div>
            </div>

            <!-- Client authorized sign-off -->
            <div class="space-y-4">
              <h4 class="font-bold text-xs uppercase text-slate-500 tracking-wider">Client Authorised Signatory</h4>
              <div class="border-b border-dashed border-slate-300 h-10 flex items-end">
                <span class="text-xs text-slate-400 italic">Sign / Stamp Here</span>
              </div>
              <div class="text-xs space-y-1 text-slate-600">
                <p><span class="font-semibold text-slate-400">Name:</span> {{ currentDoc.client_signatory_name || '_____________________' }}</p>
                <p><span class="font-semibold text-slate-400">Date:</span> {{ currentDoc.client_signatory_date || '_____________________' }}</p>
                <p><span class="font-semibold text-slate-400">Official Stamp:</span> _____________________</p>
              </div>
            </div>
          </div>

          <!-- DOCUMENT FOOTER (REPEATS CONTACT DETAILS + REF NO) -->
          <div class="border-t border-slate-200 pt-4 text-center text-[10px] text-slate-400 flex justify-between items-center">
            <div>
              <span>{{ selectedVendor?.location || 'Kenya' }} | Phone: {{ selectedVendor?.phone || '+254 700 000 000' }} | Email: {{ selectedVendor?.email || 'user@email.com' }}</span>
            </div>
            <div class="font-bold">
              <span>{{ currentDoc.reference_no }}</span>
            </div>
          </div>
        </div>

      </div>

    </div>

    <!-- TAB 3: DIRECTORIES -->
    <div v-if="activeTab === 'directories'" class="grid grid-cols-1 md:grid-cols-2 gap-8 print:hidden">
      <!-- Vendors List -->
      <div class="bg-white shadow-sm border border-slate-200 rounded-xl overflow-hidden p-5 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="text-lg font-bold text-slate-900">Vendors Directory</h3>
          <button @click="showVendorModal = true" class="text-sm font-semibold text-indigo-600 hover:text-indigo-500">
            + New Vendor
          </button>
        </div>

        <div class="space-y-3">
          <div v-for="v in vendors" :key="v.id" class="p-4 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
            <h4 class="font-bold text-slate-950 text-sm">{{ v.name }}</h4>
            <p class="text-indigo-600 text-xs font-semibold">{{ v.tagline }}</p>
            <div class="text-xs text-slate-500 pt-1 space-y-0.5">
              <p>📍 {{ v.location }}</p>
              <p>📞 {{ v.phone }}</p>
              <p>✉️ {{ v.email }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Clients List -->
      <div class="bg-white shadow-sm border border-slate-200 rounded-xl overflow-hidden p-5 space-y-4">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <h3 class="text-lg font-bold text-slate-900">Clients Directory</h3>
          <button @click="showClientModal = true" class="text-sm font-semibold text-indigo-600 hover:text-indigo-500">
            + New Client
          </button>
        </div>

        <div class="space-y-3">
          <div v-for="c in clients" :key="c.id" class="p-4 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
            <h4 class="font-bold text-slate-950 text-sm">{{ c.name }}</h4>
            <div class="text-xs text-slate-500 pt-1 space-y-0.5">
              <p>👤 Attn: {{ c.attention }}</p>
              <p>📍 {{ c.location }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODAL VENDOR CREATION (Print Hidden) -->
    <div v-if="showVendorModal" class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 flex items-center justify-center p-4 print:hidden">
      <div class="bg-white rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
        <h3 class="text-lg font-bold text-slate-900 border-b pb-2">Add Vendor Profile</h3>

        <div class="space-y-3 text-sm">
          <div>
            <label class="block text-xs font-semibold text-slate-500 uppercase">Vendor Name</label>
            <input type="text" v-model="newVendor.name" placeholder="e.g.Plants and Materials" class="mt-1 w-full rounded border px-3 py-2" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 uppercase">Tagline</label>
            <input type="text" v-model="newVendor.tagline" placeholder="e.g. Heavy Equipment Hire" class="mt-1 w-full rounded border px-3 py-2" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 uppercase">Location</label>
            <input type="text" v-model="newVendor.location" placeholder="e.g. Kenya" class="mt-1 w-full rounded border px-3 py-2" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 uppercase">Phone Number</label>
            <input type="text" v-model="newVendor.phone" placeholder="e.g. +254 700 000 000" class="mt-1 w-full rounded border px-3 py-2" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 uppercase">Email Address</label>
            <input type="email" v-model="newVendor.email" placeholder="e.g. user@email.com" class="mt-1 w-full rounded border px-3 py-2" />
          </div>
        </div>

        <div class="flex justify-end space-x-3 border-t pt-3">
          <button @click="showVendorModal = false" class="px-4 py-2 border rounded-lg text-slate-700 hover:bg-slate-50">Cancel</button>
          <button @click="createVendor" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 font-semibold">Save Vendor</button>
        </div>
      </div>
    </div>

    <!-- MODAL CLIENT CREATION (Print Hidden) -->
    <div v-if="showClientModal" class="fixed inset-0 z-50 overflow-y-auto bg-slate-900/40 flex items-center justify-center p-4 print:hidden">
      <div class="bg-white rounded-xl max-w-md w-full p-6 shadow-xl space-y-4">
        <h3 class="text-lg font-bold text-slate-900 border-b pb-2">Add Client Profile</h3>

        <div class="space-y-3 text-sm">
          <div>
            <label class="block text-xs font-semibold text-slate-500 uppercase">Client Company Name</label>
            <input type="text" v-model="newClient.name" placeholder="e.g. Golf Club" class="mt-1 w-full rounded border px-3 py-2" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 uppercase">Attention To (Representative)</label>
            <input type="text" v-model="newClient.attention" placeholder="e.g. The Club Manager" class="mt-1 w-full rounded border px-3 py-2" />
          </div>
          <div>
            <label class="block text-xs font-semibold text-slate-500 uppercase">Location Address</label>
            <input type="text" v-model="newClient.location" placeholder="e.g. Kenya" class="mt-1 w-full rounded border px-3 py-2" />
          </div>
        </div>

        <div class="flex justify-end space-x-3 border-t pt-3">
          <button @click="showClientModal = false" class="px-4 py-2 border rounded-lg text-slate-700 hover:bg-slate-50">Cancel</button>
          <button @click="createClient" class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 font-semibold">Save Client</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
/* Print stylesheet integration */
@media print {
  /* Set document size margins */
  @page {
    size: A4;
    margin: 1.5cm;
  }

  /* Reset document flow for print layout output */
  body, html {
    background-color: #fff !important;
    color: #000 !important;
    font-size: 12px !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  /* Make sure background colors render properly when generating PDFs */
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
</style>
