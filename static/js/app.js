const API_BASE = '/api';

function normalizeEndpoint(endpoint) {
    if (!endpoint.startsWith('/')) endpoint = '/' + endpoint;
    // count path segments (ignore leading/trailing slashes)
    const segments = endpoint.split('/').filter(Boolean);
    // If it's a collection root (one segment) and not already trailing slash, add '/'
    if (segments.length === 1 && !endpoint.endsWith('/')) return endpoint + '/';
    return endpoint;
}

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
        btn.addEventListener('click', () => {
            // Active State
            document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            // View Switching
            document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(`${tabId}-view`).classList.add('active');

            // Load Data
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
    modal.classList.add('show');
    // move focus to first focusable element for accessibility
    const focusable = modal.querySelector('input, select, button, [tabindex]:not([tabindex="-1"])');
    if (focusable) focusable.focus();
}

window.closeModal = function (modalId) {
    document.getElementById(modalId).classList.remove('show');
}

function setupModals() {
    window.onclick = function (event) {
        if (event.target.classList.contains('modal')) {
            event.target.classList.remove('show');
        }
    }
}

// --- Loading Data ---

async function loadDashboard() {
    const sales = await fetchAPI('/sales');
    const today = new Date().toISOString().slice(0, 10);
    let total = 0;
    sales.forEach(s => {
        if (s.date && s.date.startsWith(today)) {
            total += (s.price * s.quantity * (1 - s.discount / 100));
        }
    });
    document.getElementById('stats-sales').innerText = `$${total.toFixed(2)}`;

    const stock = await fetchAPI('/stock');
    const lowStock = stock.filter(item => item.quantity < 10).length;
    document.getElementById('stats-low-stock').innerText = lowStock;
}

async function loadProducts() {
    const data = await fetchAPI('/products');
    const tbody = document.querySelector('#products-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        (async () => {
            let ingredientsList = [];
            try {
                if (item.ingredients && item.ingredients.length) {
                    ingredientsList = item.ingredients;
                } else {
                    // Try to fetch detailed product (may include ingredients)
                    const details = await fetchAPI(`/products/${item.id}`);
                    ingredientsList = details.ingredients || [];
                }
            } catch (err) {
                ingredientsList = [];
            }

            const ingredients = ingredientsList.map(i => `${i.name}: ${i.quantity}${i.unit ? ' ' + i.unit : ''}`).join(', ') || '-';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.name}</td>
                <td>${item.price} ₽</td>
                <td>${ingredients}</td>
                <td>
                    <button onclick="editProduct(${item.id})">Edit</button>
                    <button onclick="deleteItem('products', '${item.name}')">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        })();
    });
}

async function loadStock() {
    const data = await fetchAPI('/stock');
    const tbody = document.querySelector('#stock-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.name}</td>
            <td>${item.category_id}</td>
            <td>${item.quantity}</td>
            <td>${item.unit_id}</td>
            <td><button onclick="deleteItem('stock', '${item.name}')">Delete</button></td>
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
            <td>${item.product_name}</td>
            <td>${item.quantity}</td>
            <td>${item.price}</td>
            <td>${(item.price * item.quantity).toFixed(2)}</td>
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
            <td>${item.name}</td>
            <td>${item.category_name || '-'}</td>
            <td>${item.price}</td>
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
            <td>${item.name}</td>
            <td>${item.contact_person || ''}</td>
            <td>${item.phone || ''}</td>
            <td><button onclick="deleteItem('suppliers', '${item.name}')">Delete</button></td>
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
        const type = item.product_id ? 'Product' : 'Stock';
        tr.innerHTML = `
            <td>${item.date}</td>
            <td>${type}</td>
            <td>${item.item_name || 'Unknown'}</td>
            <td>${item.quantity}</td>
            <td>${item.reason}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- Helper loaders for selects ---

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
        opt.value = c;
        opt.innerText = c;
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

    const filtered = categoryName
        ? allExpenseTypes.filter(t => t.category_name === categoryName)
        : allExpenseTypes;

    filtered.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.innerText = t.name;
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
        opt.value = s.id;
        opt.innerText = s.name;
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
        opt.value = c;
        opt.innerText = c;
        catSelect.appendChild(opt);
    });

    const products = await fetchAPI('/products');
    const stock = await fetchAPI('/stock');
    allStockItems = stock;

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
            opt.value = p.name;
            opt.innerText = p.name;
            itemSelect.appendChild(opt);
        });
    } else {
        catGroup.style.display = 'block';
        handleWriteOffCategoryChange();
    }
}

window.handleWriteOffCategoryChange = async function () {
    const categoryName = document.getElementById('writeoff-category').value;
    const itemSelect = document.getElementById('writeoff-item-select');
    itemSelect.innerHTML = '';

    if (allStockItems.length === 0) {
        allStockItems = await fetchAPI('/stock');
    }

    const filtered = categoryName
        ? allStockItems.filter(i => i.category_name === categoryName)
        : allStockItems;

    filtered.forEach(i => {
        const opt = document.createElement('option');
        opt.value = i.name;
        opt.innerText = i.name;
        itemSelect.appendChild(opt);
    });
}

// --- Forms ---

function setupForms() {
    document.getElementById('product-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        try {
            data.ingredients = JSON.parse(data.ingredients_json || '[]');
        } catch (err) {
            alert("Invalid ingredients");
            return;
        }
        try {
            if (window.editingProductId) {
                await putAPI(`/products/${window.editingProductId}`, data);
                window.editingProductId = null;
            } else {
                await postAPI('/products/', data);
            }
        } catch (err) {
            // postAPI/putAPI will have alerted
            return;
        }
        closeModal('product-modal');
        loadProducts();
    };

    document.getElementById('ingredient-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        await postAPI('/ingredients/', data);
        closeModal('ingredient-modal');
        loadIngredients();
    };

    document.getElementById('stock-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        await postAPI('/stock/', data);
        closeModal('stock-modal');
        loadStock();
    };

    document.getElementById('sale-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        await postAPI('/sales/', data);
        closeModal('sale-modal');
        loadSales();
    };

    document.getElementById('expense-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        if (!data.supplier_id) delete data.supplier_id;
        await postAPI('/expenses/', data);
        closeModal('expense-modal');
        loadExpenses();
    };

    document.getElementById('supplier-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        await postAPI('/suppliers/', data);
        closeModal('supplier-modal');
        loadSuppliers();
    };

    document.getElementById('writeoff-form').onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData.entries());
        await postAPI('/writeoffs/', data);
        closeModal('writeoff-modal');
        loadWriteOffs();
    };
}

// --- Ingredients & Recipe Logic ---

async function loadIngredients() {
    const data = await fetchAPI('/ingredients');
    const tbody = document.querySelector('#ingredients-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.name}</td>
            <td>${item.unit_name || item.unit_id}</td>
        `;
        tbody.appendChild(tr);
    });
}

let currentRecipe = [];

async function loadIngredientsForRecipe() {
    const data = await fetchAPI('/ingredients');
    const select = document.getElementById('recipe-ingredient-select');
    if (!select) return;
    select.innerHTML = '<option value="">Select Ingredient...</option>';
    // populate select and ingredientsMap
    window.ingredientsMap = {};
    data.forEach(i => {
        const opt = document.createElement('option');
        opt.value = i.name;
        opt.innerText = i.name;
        const unit = i.unit_name || i.unit_id || '';
        if (unit) opt.dataset.unit = unit;
        select.appendChild(opt);
        window.ingredientsMap[i.name] = unit;
    });

    // update unit display when changing selection
    const qtyUnit = document.getElementById('recipe-quantity-unit');
    select.addEventListener('change', () => {
        const u = select.selectedOptions[0] && select.selectedOptions[0].dataset.unit ? select.selectedOptions[0].dataset.unit : '';
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
        alert("Please select an ingredient and enter a valid quantity.");
        return;
    }
    const unit = window.ingredientsMap[name] || '';
    currentRecipe.push({ name, quantity, unit });
    updateRecipeList();
    select.value = "";
    qtyInput.value = "";
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
        const unitText = ing.unit ? ` ${ing.unit}` : '';
        li.innerHTML = `
            <span>${ing.name} - ${ing.quantity}${unitText}</span>
            <button type="button" class="btn-small-danger" onclick="removeIngredientFromRecipe(${index})">Remove</button>
        `;
        list.appendChild(li);
    });
    const jsonInput = document.getElementById('recipe-json');
    if (jsonInput) jsonInput.value = JSON.stringify(currentRecipe);
}

// Hook into openModal to init modals
const _originalOpenModal = window.openModal;
window.openModal = function (modalId) {
    _originalOpenModal(modalId);
    if (modalId === 'product-modal') {
        // Only auto-load ingredients when creating a new product.
        if (!window.editingProductId) {
            currentRecipe = [];
            loadIngredientsForRecipe();
        }
    } else if (modalId === 'writeoff-modal') {
        loadWriteOffModalData();
    } else if (modalId === 'expense-modal') {
        loadExpenseCategories();
        loadExpenseTypesForSelect();
    }
}

// PUT helper
async function putAPI(endpoint, data) {
    const url = `${API_BASE}${normalizeEndpoint(endpoint)}`;
    const res = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const err = await res.json();
        alert(`Error: ${err.detail || res.statusText}`);
        throw new Error(err.detail || res.statusText);
    }
    return await res.json();
}

window.editProduct = async function (id) {
    try {
        const prod = await fetchAPI(`/products/${id}`);
        // Populate form
        const form = document.getElementById('product-form');
        form.elements['name'].value = prod.name;
        form.elements['price'].value = prod.price;
        // Set current recipe and editing id
        currentRecipe = prod.ingredients || [];
        window.editingProductId = id;
        // Load ingredient options and update recipe list
        await loadIngredientsForRecipe();
        updateRecipeList();
        openModal('product-modal');
    } catch (err) {
        console.error(err);
        alert('Failed to load product for editing');
    }
}

// --- API Helpers ---

async function fetchAPI(endpoint) {
    const url = `${API_BASE}${normalizeEndpoint(endpoint)}`;
    const res = await fetch(url);
    if (!res.ok) {
        alert(`Error: ${res.statusText}`);
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
        alert(`Error: ${err.detail || res.statusText}`);
        throw new Error(err.detail);
    }
    return await res.json();
}

window.deleteItem = async function (resource, id) {
    if (!confirm('Are you sure?')) return;
    const res = await fetch(`${API_BASE}${normalizeEndpoint(resource + '/' + id)}`, {
        method: 'DELETE'
    });
    if (res.ok) {
        const activeTab = document.querySelector('.nav-btn.active').getAttribute('data-tab');
        loadTab(activeTab);
    } else {
        alert("Failed to delete");
    }
}
