const API_BASE = '/api';

// --- UI Logic ---

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupModals();
    setupForms();
    loadDashboard();
});

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
}

// --- Modals ---

window.openModal = function (modalId) {
    document.getElementById(modalId).style.display = 'block';
}

window.closeModal = function (modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function setupModals() {
    window.onclick = function (event) {
        if (event.target.classList.contains('modal')) {
            event.target.style.display = "none";
        }
    }
}

// --- Loading Data ---

async function loadDashboard() {
    // Determine sales today
    const sales = await fetchAPI('/sales');
    const today = new Date().toISOString().slice(0, 10);
    // Simple mock logic for "Today" as backend stores string dates e.g. "2023-10-27 10:00"
    // We'd ideally need a backend endpoint for stats.
    // For now executing client side calc.
    let total = 0;
    sales.forEach(s => {
        if (s.date && s.date.startsWith(today)) {
            total += (s.price * s.quantity * (1 - s.discount / 100));
        }
    });
    document.getElementById('stats-sales').innerText = `$${total.toFixed(2)}`;

    // Low stock
    const stock = await fetchAPI('/stock');
    const lowStock = stock.filter(item => item.quantity < 10).length; // Arbitrary threshold
    document.getElementById('stats-low-stock').innerText = lowStock;
}

async function loadProducts() {
    const data = await fetchAPI('/products');
    const tbody = document.querySelector('#products-table tbody');
    tbody.innerHTML = '';
    data.forEach(item => {
        const ingredients = item.ingredients.map(i => `${i.name}: ${i.quantity}`).join(', ');
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.name}</td>
            <td>${item.price}</td>
            <td>${ingredients}</td>
            <td><button onclick="deleteItem('products', '${item.name}')">Delete</button></td>
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
            <td>${item.name}</td>
            <td>${item.category_id}</td> <!-- Showing ID for now, ideally Name -->
            <td>${item.quantity}</td>
            <td>${item.unit_id}</td> <!-- Showing ID for now, ideally Name -->
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
            <td>${item.type_id}</td> 
            <td>${item.name}</td>
            <td>${item.price}</td>
            <td>${item.quantity}</td>
            <td>${item.supplier_id || '-'}</td>
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

// --- Helper loaders for selects ---

async function loadProductsForSelect() {
    const data = await fetchAPI('/products');
    const select = document.getElementById('sale-product-select');
    select.innerHTML = '';
    data.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.id;
        opt.innerText = p.name;
        select.appendChild(opt);
    });
}

async function loadExpenseTypesForSelect() {
    const data = await fetchAPI('/expenses/types');
    const select = document.getElementById('expense-type-select');
    select.innerHTML = '';
    data.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.innerText = t.name;
        select.appendChild(opt);
    });
}

async function loadSuppliersForSelect() {
    const data = await fetchAPI('/suppliers');
    const select = document.getElementById('expense-supplier-select');
    // Clear but keep first "No Supplier" option
    select.innerHTML = '<option value="">No Supplier</option>';
    data.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id;
        opt.innerText = s.name;
        select.appendChild(opt);
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
        await postAPI('/products/', data);
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
    select.innerHTML = '<option value="">Select Ingredient...</option>';
    data.forEach(i => {
        const opt = document.createElement('option');
        opt.value = i.name; // Product API expects name, not ID in ingredients list
        opt.innerText = i.name;
        select.appendChild(opt);
    });

    // Reset recipe state
    currentRecipe = [];
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

    currentRecipe.push({ name, quantity });
    updateRecipeList();

    // Reset inputs
    select.value = "";
    qtyInput.value = "";
}

window.removeIngredientFromRecipe = function (index) {
    currentRecipe.splice(index, 1);
    updateRecipeList();
}

function updateRecipeList() {
    const list = document.getElementById('recipe-list');
    list.innerHTML = '';
    currentRecipe.forEach((ing, index) => {
        const li = document.createElement('li');
        li.innerHTML = `
            <span>${ing.name} - ${ing.quantity}</span>
            <button type="button" class="btn-small-danger" onclick="removeIngredientFromRecipe(${index})">Remove</button>
        `;
        list.appendChild(li);
    });
    document.getElementById('recipe-json').value = JSON.stringify(currentRecipe);
}

// Hook into openModal to init recipe editor
const _originalOpenModal = window.openModal;
window.openModal = function (modalId) {
    _originalOpenModal(modalId);
    if (modalId === 'product-modal') {
        loadIngredientsForRecipe();
    }
}

// --- API Helpers ---

async function fetchAPI(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`);
    if (!res.ok) {
        alert(`Error: ${res.statusText}`);
        return [];
    }
    return await res.json();
}

async function postAPI(endpoint, data) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
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
    const res = await fetch(`${API_BASE}/${resource}/${id}`, {
        method: 'DELETE'
    });
    if (res.ok) {
        // Refresh current tab
        const activeTab = document.querySelector('.nav-btn.active').getAttribute('data-tab');
        loadTab(activeTab);
    } else {
        alert("Failed to delete");
    }
}
