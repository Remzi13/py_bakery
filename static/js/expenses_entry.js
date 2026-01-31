// Expenses Entry Logic

document.addEventListener('DOMContentLoaded', () => {
    // Set default date to now
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('doc-date').value = now.toISOString().slice(0, 16);

    // Initial translation
    if (typeof updatePageLanguage === 'function') {
        updatePageLanguage();
    }
});

// Item List Management
const itemsList = document.getElementById('expense-items-list');
const emptyState = document.getElementById('empty-state');
const totalDisplay = document.getElementById('total-display');

function updateSummary() {
    const rows = itemsList.querySelectorAll('.expense-item-row');
    let total = 0;
    rows.forEach(row => {
        const price = parseFloat(row.querySelector('.price-input').value) || 0;
        total += price;
    });
    totalDisplay.innerText = total.toFixed(2) + ' ₽';

    if (rows.length > 0) {
        emptyState.style.display = 'none';
    } else {
        emptyState.style.display = 'block';
    }
}

function addItem(id, name, price, unitId) {
    const idx = Date.now() + Math.random();
    const row = document.createElement('div');
    row.className = 'expense-item-row';
    row.innerHTML = `
        <div class="item-name">${name}</div>
        <div>
            <input type="number" step="0.01" value="1" class="item-input qty-input" name="items[${idx}][quantity]">
        </div>
        <div>
            <input type="number" step="0.01" value="${price}" class="item-input price-input" name="items[${idx}][price]">
        </div>
        <input type="hidden" name="items[${idx}][expense_type_id]" value="${id}">
        <input type="hidden" name="items[${idx}][unit_id]" value="${unitId}">
        <button type="button" class="btn-remove" onclick="this.closest('.expense-item-row').remove(); updateSummary();">×</button>
    `;

    // Listen for changes to price
    row.querySelector('.price-input').addEventListener('input', updateSummary);

    itemsList.appendChild(row);
    updateSummary();
}

// Catalog Interaction
document.getElementById('catalog-grid').addEventListener('click', (e) => {
    const card = e.target.closest('.type-card');
    if (card) {
        const id = card.dataset.id;
        const name = card.dataset.name;
        const price = card.dataset.price;
        const unitId = card.dataset.unitId;
        addItem(id, name, price, unitId);
    }
});

// Search & Filter
const typeSearch = document.getElementById('type-search');
const categoryFilter = document.getElementById('category-filter');
const typeCards = document.querySelectorAll('.type-card');

function filterCatalog() {
    const query = typeSearch.value.toLowerCase();
    const category = categoryFilter.value;

    typeCards.forEach(card => {
        const name = card.dataset.name.toLowerCase();
        const cardCategory = card.dataset.category;

        const matchesSearch = name.includes(query);
        const matchesCategory = !category || cardCategory === category;

        if (matchesSearch && matchesCategory) {
            card.style.display = 'flex';
        } else {
            card.style.display = 'none';
        }
    });
}

typeSearch.addEventListener('input', filterCatalog);
categoryFilter.addEventListener('change', filterCatalog);

// Form Reset
function resetExpenseForm() {
    const form = document.getElementById('expense-doc-form');
    form.reset();
    itemsList.innerHTML = '';

    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('doc-date').value = now.toISOString().slice(0, 16);

    updateSummary();
    showToast(t('documentSavedSuccessfully') || 'Document saved successfully');
}

// Toast Notification
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

// HTMX Success/Error handling
document.body.addEventListener('htmx:responseError', function (evt) {
    showToast(evt.detail.xhr.responseText || 'Error saving document', 'error');
});
