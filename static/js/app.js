const API_BASE = '/api';

function normalizeEndpoint(endpoint) {
    if (!endpoint.startsWith('/')) endpoint = '/' + endpoint;
    const segments = endpoint.split('/').filter(Boolean);
    if (segments.length === 1 && !endpoint.endsWith('/')) return endpoint + '/';
    return endpoint;
}

function askConfirmation(message) {
    return new Promise((resolve) => {
        const overlay = document.getElementById('modal-overlay');
        const confirmBtn = document.getElementById('modal-confirm');
        const cancelBtn = document.getElementById('modal-cancel');
        const messageElem = document.getElementById('modal-message');

        messageElem.textContent = message;
        overlay.style.display = 'flex';

        confirmBtn.onclick = () => {
            overlay.style.display = 'none';
            resolve(true);
        };
        cancelBtn.onclick = () => {
            overlay.style.display = 'none';
            resolve(false);
        };
    });
}

// --- Global Constants ---
const CURRENCY = '₽';

// --- UI Logic ---

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupModals();
    setupForms();
    loadDashboard();
});

window.editingProductId = null;
window.materialsMap = {}; // name -> unit (e.g., 'kg', 'g')

function setupTabs() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        if (btn.tagName === 'A') return; // Skip documentation link
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            const tabId = btn.getAttribute('data-tab');
            const i18nKey = btn.getAttribute('data-i18n');
            document.getElementById(`${tabId}-view`).classList.add('active');

            // Update Page Title with translation
            if (i18nKey) {
                document.getElementById('page-title').innerText = t(i18nKey);
            } else {
                document.getElementById('page-title').innerText = btn.innerText;
            }

            loadTab(tabId);
        });
    });
}

function loadTab(tabId) {
    if (tabId === 'dashboard') loadDashboard();
    if (tabId === 'products') loadProducts();
    if (tabId === 'stock') loadStock();
    if (tabId === 'sales') { /* Handled by HTMX */ }
    if (tabId === 'expenses') { loadExpenses(); loadExpenseTypesForSelect(); loadSuppliersForSelect(); }
    if (tabId === 'suppliers') loadSuppliers();
    if (tabId === 'writeoffs') loadWriteOffs();
    if (tabId === 'orders') loadOrders();
}

// --- Modals ---

window.openModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (!modal) return;
    modal.classList.add('show');
    const focusable = modal.querySelector('input, select, button, [tabindex]:not([tabindex="-1"])');
    if (focusable) focusable.focus();
}

window.closeModal = function (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('show');
}

function setupModals() {
    window.onclick = function (event) {
        if (event.target.classList.contains('modal')) {
            event.target.classList.remove('show');
        }
    }
}

// --- Smart Dashboard ---

async function loadDashboard() {
    try {
        const sales = await fetchAPI('/sales');
        const today = new Date().toISOString().slice(0, 10);

        let dailyTotal = 0;
        let weeklySales = Array(7).fill(0);
        const now = new Date();

        sales.forEach(s => {
            const saleDate = new Date(s.date.replace(' ', 'T'));
            const saleTotal = s.price * s.quantity * (1 - s.discount / 100);

            // Daily Total
            if (s.date && s.date.startsWith(today)) {
                dailyTotal += saleTotal;
            }

            // Weekly Trend
            const diffDays = Math.floor((now - saleDate) / (1000 * 60 * 60 * 24));
            if (diffDays >= 0 && diffDays < 7) {
                weeklySales[6 - diffDays] += saleTotal;
            }
        });

        document.getElementById('stats-sales').innerText = `${dailyTotal.toFixed(2)} ${CURRENCY}`;

        // Render Chart — ensure left-to-right order: oldest -> newest
        const chart = document.getElementById('sales-chart');
        chart.innerHTML = '';
        const maxSale = Math.max(...weeklySales, 1);

        // Create bars for 6 days ago .. today so they render left-to-right
        const weekdayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        for (let i = 0; i < 7; i++) {
            const val = weeklySales[i] || 0;
            const bar = document.createElement('div');
            bar.className = 'chart-bar';
            bar.style.height = `${(val / maxSale) * 100}%`;

            const barDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - (6 - i));
            const dayLabel = weekdayNames[barDate.getDay()];
            bar.setAttribute('data-label', dayLabel);
            bar.title = `${dayLabel}: ${val.toFixed(2)} ${CURRENCY}`;
            chart.appendChild(bar);
        }

        const stock = await fetchAPI('/stock');
        const lowStock = stock.filter(item => item.quantity < 10).length;
        document.getElementById('stats-low-stock').innerText = lowStock;

        // Recent Activity (Simple feed of latest actions)
        const recentActivity = document.getElementById('recent-activity');
        recentActivity.innerHTML = '';
        const sortedSales = sales.sort((a, b) => new Date(b.date) - new Date(a.date)).slice(0, 5);
        sortedSales.forEach(s => {
            const item = document.createElement('div');
            item.style.fontSize = '0.85rem';
            item.innerHTML = `<strong>Sold:</strong> ${s.product_name} x ${s.quantity} <span style="float:right; opacity:0.6">${s.date.split(' ')[1]}</span>`;
            recentActivity.appendChild(item);
        });

        loadPendingOrders();

    } catch (err) {
        showToast("Failed to load dashboard data", "error");
    }
}

async function loadPendingOrders() {
    try {
        const data = await fetchAPI('/orders/pending');
        const list = document.getElementById('pending-orders-list');
        if (!list) return;

        if (data.length === 0) {
            list.innerHTML = `<p style="color: var(--text-muted); font-size: 0.9rem;" data-i18n="noPendingOrders">${t('noPendingOrders')}</p>`;
            return;
        }

        list.innerHTML = data.map(order => {
            const total = order.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
            return `
                <div class="card" style="padding: 10px; border-left: 4px solid var(--primary-color);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 5px;">
                        <strong>#${order.id}</strong>
                        <span style="font-size: 0.75rem; color: var(--text-muted)">${order.completion_date || '-'}</span>
                    </div>
                    <div style="font-size: 0.85rem; margin-bottom: 8px;">
                        ${order.items.map(i => `${i.product_name} x ${i.quantity}`).join(', ')}
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600;">${total.toFixed(2)} ${CURRENCY}</span>
                        <div style="display: flex; gap: 8px;">
                            <button class="btn-primary" style="padding: 4px 10px; font-size: 0.8rem;" onclick="infoOrder(${order.id})">${t('infoOrder')}</button>
                            <button class="btn-primary" style="padding: 4px 10px; font-size: 0.8rem;" onclick="completeOrder(${order.id})">${t('completeOrder')}</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        console.error("Failed to load pending orders", err);
    }
}

// --- List Loading ---

async function loadProducts() {
    const data = await fetchAPI('/products');
    const tbody = document.querySelector('#products-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const materials = item.materials.map(i => `${i.name}: ${i.quantity}${i.unit ? ' ' + i.unit : ''}`).join(', ') || '-';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${item.name}</strong></td>
            <td>${item.price} ${CURRENCY}</td>
            <td style="font-size: 0.85rem; color: var(--text-muted)">${materials}</td>
            <td>
                <div style="display:flex; gap:8px;">
                    <button class="btn-icon" title="Edit" onclick="editProduct(${item.id})">✏️</button>
                    <button class="btn-icon" title="Delete" onclick="deleteItem('products', '${item.name}')">🗑️</button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadStock() {
    const data = await fetchAPI('/stock');
    const tbody = document.querySelector('#stock-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${item.name}</strong></td>
            <td><span style="font-size: 0.75rem; background: var(--accent-light); padding: 2px 8px; border-radius: 12px; font-weight: 600;">${item.category_name}</span></td>
            <td>${Number(item.quantity).toFixed(2)}</td>
            <td>${item.unit_name}</td>
            <td>
                <div style="display:flex; gap:8px;">
                    <button class="btn-icon" title="Edit" onclick="editStock(${item.id})">✏️</button>
                    <button class="btn-icon" title="Delete" onclick="deleteItem('stock', '${item.name}')">🗑️</button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}


async function loadExpenses() {
    const data = await fetchAPI('/expenses/documents');
    const tbody = document.querySelector('#expenses-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.date}</td>
            <td><strong>${item.supplier_name || '-'}</strong></td>
            <td>${item.items_count}</td>
            <td>${item.total_amount} ${CURRENCY}</td>
            <td>${item.comment || ''}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- Expense Document Logic ---

let currentExpenseItems = [];

window.addExpenseItemRow = function () {
    const typeSelect = document.getElementById('expense-item-type');
    const qtyInput = document.getElementById('expense-item-qty');
    const unitSelect = document.getElementById('expense-item-unit');
    const priceInput = document.getElementById('expense-item-price');

    const typeId = typeSelect.value;
    const typeName = typeSelect.options[typeSelect.selectedIndex]?.text;
    const quantity = parseFloat(qtyInput.value);
    const unitId = unitSelect.value;
    const unitName = unitSelect.options[unitSelect.selectedIndex]?.text;
    const price = parseFloat(priceInput.value);

    if (!typeId || !quantity || !unitId || isNaN(price)) {
        showToast("Please fill all item fields", "error");
        return;
    }

    currentExpenseItems.push({
        expense_type_id: parseInt(typeId),
        expense_type_name: typeName,
        quantity: quantity,
        unit_id: parseInt(unitId),
        unit_name: unitName,
        price_per_unit: price
    });

    updateExpenseItemsList();

    // clear inputs
    qtyInput.value = '';
    priceInput.value = '';
}

window.removeExpenseItemRow = function (index) {
    currentExpenseItems.splice(index, 1);
    updateExpenseItemsList();
}

function updateExpenseItemsList() {
    const list = document.getElementById('expense-items-list');
    if (!list) return;
    list.innerHTML = '';
    let total = 0;
    currentExpenseItems.forEach((item, index) => {
        const itemTotal = item.quantity * item.price_per_unit;
        total += itemTotal;
        const li = document.createElement('li');
        li.className = 'recipe-item';
        li.innerHTML = `
            <span><strong>${item.expense_type_name}</strong>: ${item.quantity} ${item.unit_name} x ${item.price_per_unit} = ${itemTotal.toFixed(2)}</span>
            <button type="button" onclick="removeExpenseItemRow(${index})">×</button>
        `;
        list.appendChild(li);
    });
    document.getElementById('expense-doc-total').innerText = total.toFixed(2);
}

async function loadExpenseDocumentModalData() {
    // Set current date
    const now = new Date();
    // Adjust to local timezone ISO string (YYYY-MM-DDTHH:MM)
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('expense-doc-date').value = now.toISOString().slice(0, 16);

    // Load Suppliers
    const suppliers = await fetchAPI('/suppliers');
    const supplierSelect = document.getElementById('expense-doc-supplier');
    supplierSelect.innerHTML = '<option value="">Select Supplier...</option>';
    suppliers.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id; opt.innerText = s.name;
        supplierSelect.appendChild(opt);
    });

    // Load Categories for Item Filter
    const categories = await fetchAPI('/expenses/categories');
    const catSelect = document.getElementById('expense-item-category');
    catSelect.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c; opt.innerText = c;
        catSelect.appendChild(opt);
    });

    // Load Expense Types and init filter
    await loadExpenseTypesForDoc();

    // Load Units ...
    const unitSelect = document.getElementById('expense-item-unit');
    unitSelect.innerHTML = `
        <option value="1">kg</option>
        <option value="2">g</option>
        <option value="3">l</option>
        <option value="4">pc</option>
    `;
}

let docExpenseTypes = [];

async function loadExpenseTypesForDoc() {
    docExpenseTypes = await fetchAPI('/expenses/types');
    filterDocExpenseTypes();
}

window.filterDocExpenseTypes = function () {
    const category = document.getElementById('expense-item-category').value;
    const select = document.getElementById('expense-item-type');
    select.innerHTML = '<option value="">Select Expense Type...</option>';

    const filtered = category ? docExpenseTypes.filter(t => t.category_name === category) : docExpenseTypes;

    filtered.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.innerText = t.name;
        if (t.default_price) {
            opt.dataset.price = t.default_price;
        }
        select.appendChild(opt);
    });

    // Auto-fill price on change
    select.onchange = () => {
        const price = select.selectedOptions[0]?.dataset.price;
        if (price) document.getElementById('expense-item-price').value = price;
    };
}


async function loadSuppliers() {
    const data = await fetchAPI('/suppliers');
    const tbody = document.querySelector('#suppliers-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${item.name}</strong></td>
            <td>${item.contact_person || ''}</td>
            <td>${item.phone || ''}</td>
            <td><button class="btn-icon" title="Delete" onclick="deleteItem('suppliers', '${item.name}')">🗑️</button></td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadWriteOffs() {
    const data = await fetchAPI('/writeoffs');
    const tbody = document.querySelector('#writeoffs-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        const typeLabel = item.product_id ? 'Product' : 'Stock';
        tr.innerHTML = `
            <td>${item.date}</td>
            <td><span style="font-size:0.7rem; opacity:0.7">${typeLabel}</span></td>
            <td><strong>${item.item_name}</strong></td>
            <td>${item.quantity}</td>
            <td><span style="color:var(--text-muted)">${item.reason}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadOrders() {
    const data = await fetchAPI('/orders');
    const tbody = document.querySelector('#orders-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';

    data.forEach(order => {
        const total = order.items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        const tr = document.createElement('tr');
        const statusClass = order.status === 'completed' ? 'trend-up' : 'trend-down';

        tr.innerHTML = `
            <td>#${order.id}</td>            
            <td>${order.completion_date || '-'}</td>
            <td><span class="stat-trend ${statusClass}">${t('status' + order.status.charAt(0).toUpperCase() + order.status.slice(1))}</span></td>
            <td style="font-size: 0.85rem;">${order.items.map(i => `${i.product_name} x ${i.quantity}`).join('<br>')}</td>
            <td><strong>${total.toFixed(2)} ${CURRENCY}</strong></td>
            <td>
                <div style="display:flex; gap:8px;">
                    <button class="btn-icon" title="${t('infoOrder')}" onclick="infoOrder(${order.id})">ℹ️</button>
                    ${order.status === 'pending' ?
                `<button class="btn-icon" title="${t('completeOrder')}" onclick="completeOrder(${order.id})">✅</button>
                    <button class="btn-icon" title="Delete" onclick="deleteOrder(${order.id})">🗑️</button>` : ''}                    
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

window.infoOrder = async function (orderId) {
    try {
        const order = await fetchAPI(`/orders/${orderId}`);
        let infoHtml = `<h3>${t('orderDetails')} #${order.id}</h3>`;
        infoHtml += `<p><strong>${t('completionDate')}:</strong> ${order.completion_date || '-'}</p>`;
        infoHtml += `<p><strong>${t('status')}:</strong> ${t('status' + order.status.charAt(0).toUpperCase() + order.status.slice(1))}</p>`;

        if (order.additional_info) {
            infoHtml += `
                <div class="info-comment-box">
                    <strong>${t('additionalInfo')}:</strong>
                    <p>${order.additional_info}</p>
                </div>`;
        }

        infoHtml += `<h4>${t('items')}:</h4><ul>`;

        order.items.forEach(item => {
            const priceFixed = Number(item.price).toFixed(2);
            const totalItem = (item.quantity * item.price).toFixed(2);
            infoHtml += `<li>
                <span>${item.product_name} <strong>x ${item.quantity}</strong></span>
                <span>${priceFixed} ${CURRENCY} (Total: ${totalItem} ${CURRENCY})</span>
            </li>`;
        });

        infoHtml += `</ul>`;

        const modalContent = document.getElementById('order-info-modal-content');
        modalContent.innerHTML = infoHtml;
        openModal('order-info-modal');
    } catch (err) {
        console.error(err);
        showToast("Failed to load order info", "error");
    }
}

window.completeOrder = async function (orderId) {
    if (!confirm(t('confirmCompleteOrder') || 'Complete this order?')) return;
    try {
        const res = await fetch(`${API_BASE}/orders/${orderId}/complete`, {
            method: 'POST'
        });
        if (res.ok) {
            showToast("Order completed successfully!");
            const activeTab = document.querySelector('.nav-btn.active').getAttribute('data-tab');
            if (activeTab === 'dashboard') loadDashboard();
            else if (activeTab === 'orders') loadOrders();
        } else {
            const err = await res.json();
            showToast(`Error: ${err.detail || 'Failed to complete order'}`, 'error');
        }
    } catch (err) {
        showToast("Connection error", "error");
    }
}

window.deleteOrder = async function (orderId) {
    if (!confirm('Are you sure you want to delete this order?')) return;
    try {
        const res = await fetch(`${API_BASE}/orders/${orderId}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            showToast("Order deleted");
            loadOrders();
        } else {
            showToast("Failed to delete order", "error");
        }
    } catch (err) {
        showToast("Connection error", "error");
    }
}

// --- Smart Filtering ---

window.filterTable = function (tableId, query) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    const rows = tbody.querySelectorAll('tr');
    const filter = query.toLowerCase();

    rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
}

// --- Form Helpers ---


let allExpenseTypes = [];
async function loadExpenseCategories() {
    const categories = await fetchAPI('/expenses/categories');
    const select = document.getElementById('expense-category-filter');
    if (!select) return;
    select.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c; opt.innerText = c;
        select.appendChild(opt);
    });
}

async function loadExpenseTypesForSelect() {
    const data = await fetchAPI('/expenses/types');
    allExpenseTypes = data;
    handleExpenseCategoryChange();
}

window.handleExpenseCategoryChange = function () {
    const categoryName = document.getElementById('expense-category-filter').value;
    const select = document.getElementById('expense-type-select');
    if (!select) return;
    select.innerHTML = '';
    const filtered = categoryName ? allExpenseTypes.filter(t => t.category_name === categoryName) : allExpenseTypes;
    filtered.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id; opt.innerText = t.name;
        select.appendChild(opt);
    });
}

async function loadSuppliersForSelect() {
    const data = await fetchAPI('/suppliers');
    const select = document.getElementById('expense-supplier-select');
    if (!select) return;
    select.innerHTML = '<option value="">No Supplier</option>';
    data.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id; opt.innerText = s.name;
        select.appendChild(opt);
    });
}

let allStockItems = [];
async function loadWriteOffModalData() {
    const categories = await fetchAPI('/stock/categories');
    const catSelect = document.getElementById('writeoff-category');
    catSelect.innerHTML = '<option value="">All Categories</option>';
    categories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c; opt.innerText = c;
        catSelect.appendChild(opt);
    });
    allStockItems = await fetchAPI('/stock');
    handleWriteOffTypeChange();
}

window.handleWriteOffTypeChange = async function () {
    const type = document.getElementById('writeoff-type').value;
    const catGroup = document.getElementById('writeoff-category-group');
    const itemSelect = document.getElementById('writeoff-item-select');
    itemSelect.innerHTML = '';
    if (type === 'product') {
        catGroup.style.display = 'none';
        const products = await fetchAPI('/products');
        products.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.name; opt.innerText = p.name;
            itemSelect.appendChild(opt);
        });
    } else {
        catGroup.style.display = 'block';
        handleWriteOffCategoryChange();
    }
}

window.handleWriteOffCategoryChange = function () {
    const categoryName = document.getElementById('writeoff-category').value;
    const itemSelect = document.getElementById('writeoff-item-select');
    itemSelect.innerHTML = '';
    const filtered = categoryName ? allStockItems.filter(i => i.category_name === categoryName) : allStockItems;
    filtered.forEach(i => {
        const opt = document.createElement('option');
        opt.value = i.name; opt.innerText = i.name;
        itemSelect.appendChild(opt);
    });
}

// --- Notifications ---

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${type === 'error' ? '❌' : '✅'}</span> ${message}`;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- Form Setup ---

// --- Form Setup ---

function setupForms() {
    const forms = [
        { id: 'product-form', endpoint: '/products/', tab: 'products', modal: 'product-modal' },
        { id: 'stock-form', endpoint: '/stock/', tab: 'stock', modal: 'stock-modal' },

        // New Expense Forms
        { id: 'expense-document-form', endpoint: '/expenses/documents', tab: 'expenses', modal: 'expense-document-modal' },
        { id: 'expense-category-form', endpoint: '/expenses/categories', tab: 'expenses', modal: 'expense-category-modal' },
        { id: 'expense-type-form', endpoint: '/expenses/types', tab: 'expenses', modal: 'expense-type-modal' },

        { id: 'supplier-form', endpoint: '/suppliers/', tab: 'suppliers', modal: 'supplier-modal' },
        { id: 'writeoff-form', endpoint: '/writeoffs/', tab: 'writeoffs', modal: 'writeoff-modal' }
    ];

    forms.forEach(f => {
        const form = document.getElementById(f.id);
        if (!form) return;
        form.onsubmit = async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());

            if (f.id === 'product-form') {
                try { data.materials = JSON.parse(data.materials_json || '[]'); }
                catch (err) { showToast("Invalid recipe", "error"); return; }
            }
            if (f.id === 'expense-document-form') {
                if (currentExpenseItems.length === 0) {
                    showToast("Add at least one item", "error");
                    return;
                }
                data.items = currentExpenseItems;
                // date format fix if needed? datetime-local is YYYY-MM-DDTHH:MM. Pydantic expects string.
                data.date = data.date.replace('T', ' ');
            }
            if (f.id === 'expense-type-form') {
                data.stock = form.querySelector('[name="stock"]').checked;
            }

            if (f.id === 'stock-form') {
                const itemId = data.id;
                try {
                    if (itemId) {
                        const updatePayload = { quantity: parseFloat(data.quantity) };
                        const itemName = encodeURIComponent(data.name);
                        await putAPI(`/stock/${itemName}/set`, updatePayload);
                        showToast("Stock quantity updated!");
                    } else {

                        await postAPI(f.endpoint, data);
                        showToast("New item added!");
                    }
                    closeModal(f.modal);
                    loadTab(f.tab);
                    form.reset();
                    return;
                }
                catch (err) {
                    return;
                }
            }

            try {
                if (f.id === 'product-form' && window.editingProductId) {
                    await putAPI(`/products/${window.editingProductId}`, data);
                    window.editingProductId = null;
                } else {
                    await postAPI(f.endpoint, data);
                }
                showToast("Saved successfully!");
                closeModal(f.modal);
                loadTab(f.tab);
                form.reset();
                if (f.id === 'expense-document-form') {
                    currentExpenseItems = [];
                    updateExpenseItemsList();
                }
            } catch (err) {
                // error already shown in postAPI/putAPI
            }
        };
    });
}


// --- Recipe Handling ---

let currentRecipe = [];
async function loadIngredientsForRecipe() {
    const data = await fetchAPI('/stock/materials');
    const select = document.getElementById('recipe-ingredient-select');
    if (!select) return;
    select.innerHTML = '<option value="">Select Ingredient...</option>';
    window.materialsMap = {};
    data.forEach(i => {
        const opt = document.createElement('option');
        opt.value = i.name; opt.innerText = i.name;
        const unit = i.unit_name || '';
        opt.dataset.unit = unit;
        select.appendChild(opt);
        window.materialsMap[i.name] = unit;
    });

    const qtyUnit = document.getElementById('recipe-quantity-unit');
    select.addEventListener('change', () => {
        const u = select.selectedOptions[0]?.dataset.unit || '';
        if (qtyUnit) qtyUnit.textContent = u;
    });
}

window.addNewProduct = function () {
    window.editingProductId = null;
    const form = document.getElementById('product-form');
    if (form) form.reset();

    currentRecipe = [];
    loadIngredientsForRecipe();
    updateRecipeList();

    // Reset title to "Add Product"
    const title = document.querySelector('#product-modal h2');
    if (title) {
        title.setAttribute('data-i18n', 'addProduct');
        title.innerText = typeof t === 'function' ? t('addProduct') : 'Add Product';
    }

    openModal('product-modal');
};

window.addMaterialToProduct = function () {
    const select = document.getElementById('recipe-ingredient-select');
    const name = select.value;
    const qtyInput = document.getElementById('recipe-quantity');
    const quantity = parseFloat(qtyInput.value);
    if (!name || isNaN(quantity) || quantity <= 0) {
        showToast("Enter valid ingredient and quantity", "error");
        return;
    }
    const unit = window.materialsMap[name] || '';
    currentRecipe.push({ name, quantity, unit });
    updateRecipeList();
    select.value = ""; qtyInput.value = "";
}

window.removeIngredientFromRecipe = function (index) {
    currentRecipe.splice(index, 1);
    updateRecipeList();
}

function updateRecipeList() {
    const list = document.getElementById('recipe-list');
    if (!list) return;
    list.innerHTML = '';
    currentRecipe.forEach((ing, index) => {
        const li = document.createElement('li');
        li.className = 'recipe-item';
        li.innerHTML = `
            <span><strong>${ing.name}</strong> - ${ing.quantity} ${ing.unit}</span>
            <button type="button" onclick="removeIngredientFromRecipe(${index})">×</button>
        `;
        list.appendChild(li);
    });
    const jsonInput = document.getElementById('recipe-json');
    if (jsonInput) jsonInput.value = JSON.stringify(currentRecipe);
}

// Hook into openModal to init specific data
const _originalOpenModal = window.openModal;
window.openModal = function (modalId) {
    _originalOpenModal(modalId);

    // Note: 'product-modal' is now largely handled by addNewProduct and editProduct directly,
    // but we keep this check for consistency if openModal is called elsewhere.
    if (modalId === 'product-modal' && !window.editingProductId) {
        // Safe check, but addNewProduct does this better
    }
    else if (modalId === 'writeoff-modal') {
        loadWriteOffModalData();
    } else if (modalId === 'expense-modal') {
        // Legacy
        loadExpenseCategories();
        loadExpenseTypesForSelect();
        loadSuppliersForSelect();
    }
    else if (modalId === 'expense-document-modal') {
        loadExpenseDocumentModalData();
    }
    else if (modalId === 'expense-type-modal') {
        loadExpenseCategoriesForType();
    }
    else if (modalId === 'stock-modal') {
        loadStockCategoriesForSelect();
    }
    else if (modalId === 'sale-modal') {
        loadProductsForSelect();
    }
}

async function loadExpenseCategoriesForType() {
    const categories = await fetchAPI('/expenses/categories');
    const select = document.getElementById('expense-type-category-select');
    if (!select) return;
    select.innerHTML = '<option value="">Select Category...</option>';
    categories.forEach(c => {
        const opt = document.createElement('option');
        opt.value = c; opt.innerText = c;
        select.appendChild(opt);
    });
}

// --- API Helpers ---

async function fetchAPI(endpoint) {
    const url = `${API_BASE}${normalizeEndpoint(endpoint)}`;
    const res = await fetch(url);
    if (!res.ok) {
        showToast(`Error: ${res.statusText}`, 'error');
        return [];
    }
    return await res.json();
}

async function postAPI(endpoint, data) {
    const url = `${API_BASE}${normalizeEndpoint(endpoint)}`;
    const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const err = await res.json();
        showToast(`Error: ${err.detail || res.statusText}`, 'error');
        throw new Error(err.detail);
    }
    return await res.json();
}

async function putAPI(endpoint, data) {
    const url = `${API_BASE}${normalizeEndpoint(endpoint)}`;
    const res = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const err = await res.json();
        showToast(`Error: ${err.detail || res.statusText}`, 'error');
        throw new Error(err.detail);
    }
    return await res.json();
}

window.editProduct = async function (id) {
    try {
        const prod = await fetchAPI(`/products/${id}`);
        const form = document.getElementById('product-form');
        form.elements['name'].value = prod.name;
        form.elements['price'].value = prod.price;

        window.editingProductId = id;
        currentRecipe = prod.materials || [];

        // Load ingredients then update list
        await loadIngredientsForRecipe();
        updateRecipeList();

        // Update title to "Edit Product"
        const title = document.querySelector('#product-modal h2');
        if (title) {
            title.setAttribute('data-i18n', 'editProduct');
            title.innerText = typeof t === 'function' ? t('editProduct') : 'Edit Product';
        }

        openModal('product-modal');
    } catch (err) {
        console.error(err);
        showToast('Failed to load product', 'error');
    }
}

window.addNewStock = function () {
    const form = document.getElementById('stock-form');
    form.reset();
    form.elements['id'].value = "";

    document.querySelector('#stock-modal h2').innerText = "Add Stock Item";
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.innerText = "Add Item";

    openModal('stock-modal');
};

window.editStock = async function (id) {
    try {
        const item = await fetchAPI(`/stock/${id}`);
        const form = document.getElementById('stock-form');

        form.elements['id'].value = item.id;
        form.elements['name'].value = item.name;
        form.elements['category_name'].value = item.category_name;
        form.elements['quantity'].value = item.quantity;
        form.elements['unit_name'].value = item.unit_name;

        document.querySelector('#stock-modal h2').innerText = "Edit Stock Item";
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.innerText = "Save Changes";

        openModal('stock-modal');
    } catch (err) {
        showToast('Error loading item', 'error');
    }
};

async function loadStockCategoriesForSelect() {
    try {
        const categories = await fetchAPI('/stock/categories');
        const select = document.getElementById('stock-category-select');

        if (!select) return;

        select.innerHTML = '';

        categories.forEach(cat => {
            const opt = document.createElement('option');
            opt.value = cat;
            opt.innerText = cat;
            select.appendChild(opt);
        });
    } catch (err) {
        console.error("Failed to load stock categories", err);
    }
}

window.deleteItem = async function (resource, id) {
    const confirmed = await askConfirmation(t('deleteConfirm'));

    if (!confirmed) return;

    try {
        const endpoint = normalizeEndpoint(`${resource}/${encodeURIComponent(id)}`);
        const res = await fetch(`${API_BASE}${endpoint}`, {
            method: 'DELETE'
        });

        if (res.ok) {
            showToast("Item deleted");
            const activeTab = document.querySelector('.nav-btn.active').getAttribute('data-tab');
            loadTab(activeTab);
        } else {
            showToast("Failed to delete item", "error");
        }
    } catch (err) {
        showToast("Connection error", "error");
    }
}