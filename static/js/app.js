const API_BASE = '/api';

function normalizeEndpoint(endpoint) {
    if (!endpoint.startsWith('/')) endpoint = '/' + endpoint;
    const segments = endpoint.split('/').filter(Boolean);
    if (segments.length === 1 && !endpoint.endsWith('/')) return endpoint + '/';
    return endpoint;
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
window.ingredientsMap = {}; // name -> unit (e.g., 'kg', 'g')

function setupTabs() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        if (btn.tagName === 'A') return; // Skip documentation link
        btn.addEventListener('click', () => {
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(`${tabId}-view`).classList.add('active');
            
            // Update Page Title
            document.getElementById('page-title').innerText = btn.innerText;

            loadTab(tabId);
        });
    });
}

function loadTab(tabId) {
    if (tabId === 'dashboard') loadDashboard();
    if (tabId === 'products') loadProducts();
    if (tabId === 'stock') loadStock();
    if (tabId === 'sales') { loadSales(); loadProductsForSelect(); }
    if (tabId === 'expenses') { loadExpenses(); loadExpenseTypesForSelect(); loadSuppliersForSelect(); }
    if (tabId === 'suppliers') loadSuppliers();
    if (tabId === 'ingredients') loadIngredients();
    if (tabId === 'writeoffs') loadWriteOffs();
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

        // Render Chart
        const chart = document.getElementById('sales-chart');
        chart.innerHTML = '';
        const maxSale = Math.max(...weeklySales) || 100;
        const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        const todayIdx = now.getDay();

        weeklySales.forEach((val, i) => {
            const bar = document.createElement('div');
            bar.className = 'chart-bar';
            bar.style.height = `${(val / maxSale) * 100}%`;
            const dayLabel = days[(todayIdx - (6 - i) + 7) % 7];
            bar.setAttribute('data-label', dayLabel);
            bar.title = `${dayLabel}: ${val.toFixed(2)} ${CURRENCY}`;
            chart.appendChild(bar);
        });

        const stock = await fetchAPI('/stock');
        const lowStock = stock.filter(item => item.quantity < 10).length;
        document.getElementById('stats-low-stock').innerText = lowStock;

        // Recent Activity (Simple feed of latest actions)
        const recentActivity = document.getElementById('recent-activity');
        recentActivity.innerHTML = '';
        const sortedSales = sales.sort((a,b) => new Date(b.date) - new Date(a.date)).slice(0, 5);
        sortedSales.forEach(s => {
            const item = document.createElement('div');
            item.style.fontSize = '0.85rem';
            item.innerHTML = `<strong>Sold:</strong> ${s.product_name} x ${s.quantity} <span style="float:right; opacity:0.6">${s.date.split(' ')[1]}</span>`;
            recentActivity.appendChild(item);
        });

    } catch (err) {
        showToast("Failed to load dashboard data", "error");
    }
}

// --- List Loading ---

async function loadProducts() {
    const data = await fetchAPI('/products');
    const tbody = document.querySelector('#products-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const ingredients = item.ingredients.map(i => `${i.name}: ${i.quantity}${i.unit ? ' ' + i.unit : ''}`).join(', ') || '-';
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${item.name}</strong></td>
            <td>${item.price} ${CURRENCY}</td>
            <td style="font-size: 0.85rem; color: var(--text-muted)">${ingredients}</td>
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
            <td>${item.quantity}</td>
            <td>${item.unit_name}</td>
            <td><button class="btn-icon" title="Delete" onclick="deleteItem('stock', '${item.name}')">🗑️</button></td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadSales() {
    const data = await fetchAPI('/sales');
    const tbody = document.querySelector('#sales-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.date}</td>
            <td><strong>${item.product_name}</strong></td>
            <td>${item.quantity}</td>
            <td>${item.price} ${CURRENCY}</td>
            <td><strong>${(item.price * item.quantity * (1 - item.discount / 100)).toFixed(2)} ${CURRENCY}</strong></td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadExpenses() {
    const data = await fetchAPI('/expenses');
    const tbody = document.querySelector('#expenses-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.date}</td>
            <td><strong>${item.name}</strong></td>
            <td>${item.category_name || '-'}</td>
            <td>${item.price} ${CURRENCY}</td>
            <td>${item.quantity}</td>
            <td>${item.supplier_name || '-'}</td>
        `;
        tbody.appendChild(tr);
    });
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

async function loadIngredients() {
    const data = await fetchAPI('/ingredients');
    const tbody = document.querySelector('#ingredients-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${item.name}</strong></td>
            <td>${item.unit_name}</td>
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

// --- Smart Filtering ---

window.filterTable = function(tableId, query) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    const rows = tbody.querySelectorAll('tr');
    const filter = query.toLowerCase();
    
    rows.forEach(row => {
        const text = row.innerText.toLowerCase();
        row.style.display = text.includes(filter) ? '' : 'none';
    });
}

// --- Form Helpers ---

async function loadProductsForSelect() {
    const data = await fetchAPI('/products');
    const select = document.getElementById('sale-product-select');
    if (!select) return;
    select.innerHTML = '';
    data.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.innerText = p.name;
        select.appendChild(opt);
    });
}

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

function setupForms() {
    const forms = [
        { id: 'product-form', endpoint: '/products/', tab: 'products', modal: 'product-modal' },
        { id: 'ingredient-form', endpoint: '/ingredients/', tab: 'ingredients', modal: 'ingredient-modal' },
        { id: 'stock-form', endpoint: '/stock/', tab: 'stock', modal: 'stock-modal' },
        { id: 'sale-form', endpoint: '/sales/', tab: 'sales', modal: 'sale-modal' },
        { id: 'expense-form', endpoint: '/expenses/', tab: 'expenses', modal: 'expense-modal' },
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
                try { data.ingredients = JSON.parse(data.ingredients_json || '[]'); } 
                catch (err) { showToast("Invalid recipe", "error"); return; }
            }
            if (f.id === 'expense-form' && !data.supplier_id) delete data.supplier_id;

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
            } catch (err) {
                // error already shown in postAPI/putAPI
            }
        };
    });
}

// --- Recipe Handling ---

let currentRecipe = [];
async function loadIngredientsForRecipe() {
    const data = await fetchAPI('/ingredients');
    const select = document.getElementById('recipe-ingredient-select');
    if (!select) return;
    select.innerHTML = '<option value="">Select Ingredient...</option>';
    window.ingredientsMap = {};
    data.forEach(i => {
        const opt = document.createElement('option');
        opt.value = i.name; opt.innerText = i.name;
        const unit = i.unit_name || '';
        opt.dataset.unit = unit;
        select.appendChild(opt);
        window.ingredientsMap[i.name] = unit;
    });

    const qtyUnit = document.getElementById('recipe-quantity-unit');
    select.addEventListener('change', () => {
        const u = select.selectedOptions[0]?.dataset.unit || '';
        if (qtyUnit) qtyUnit.textContent = u;
    });
    updateRecipeList();
}

window.addIngredientToRecipe = function () {
    const select = document.getElementById('recipe-ingredient-select');
    const name = select.value;
    const qtyInput = document.getElementById('recipe-quantity');
    const quantity = parseFloat(qtyInput.value);
    if (!name || isNaN(quantity) || quantity <= 0) {
        showToast("Enter valid ingredient and quantity", "error");
        return;
    }
    const unit = window.ingredientsMap[name] || '';
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
    if (modalId === 'product-modal' && !window.editingProductId) {
        currentRecipe = []; loadIngredientsForRecipe();
    } else if (modalId === 'writeoff-modal') {
        loadWriteOffModalData();
    } else if (modalId === 'expense-modal') {
        loadExpenseCategories(); loadExpenseTypesForSelect();
        loadSuppliersForSelect();
    }
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
        currentRecipe = prod.ingredients || [];
        window.editingProductId = id;
        await loadIngredientsForRecipe();
        openModal('product-modal');
    } catch (err) {
        showToast('Failed to load product', 'error');
    }
}

window.deleteItem = async function (resource, id) {
    if (!confirm('Are you sure you want to delete this?')) return;
    try {
        const res = await fetch(`${API_BASE}${normalizeEndpoint(resource + '/' + id)}`, { 
            method: 'DELETE' 
        });
        if (res.ok) {
            showToast("Item deleted");
            const activeTab = document.querySelector('.nav-btn.active').getAttribute('data-tab');
            loadTab(activeTab);
        } else {
            showToast("Failed to delete item. It might be in use.", "error");
        }
    } catch (err) {
        showToast("Connection error", "error");
    }
}
