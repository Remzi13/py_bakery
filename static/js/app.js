// --- Constants ---
const CURRENCY = '₽';

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    // Basic setup if needed
});

// --- HTMX Event Listeners ---

// Navigation active state and title update
document.body.addEventListener('htmx:beforeRequest', function (evt) {
    const trigger = evt.detail.elt;
    if (trigger.classList.contains('nav-btn')) {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        trigger.classList.add('active');

        const i18nKey = trigger.getAttribute('data-i18n') || trigger.getAttribute('data-tab');
        if (i18nKey) {
            const titleElem = document.getElementById('page-title');
            if (titleElem) titleElem.innerText = typeof t === 'function' ? t(i18nKey) : i18nKey;
        }
    }
});

// Custom confirmation modal for hx-confirm
document.body.addEventListener('htmx:confirm', function (evt) {
    const message = evt.detail.question;
    if (message) {
        evt.preventDefault();
        askConfirmation(message).then(function (confirmed) {
            if (confirmed) {
                evt.detail.issueRequest(true);
            }
        });
    }
});

// Generic error handling for HTMX
document.body.addEventListener('htmx:responseError', function (evt) {
    const error = evt.detail.xhr.responseText || 'An error occurred';
    showToast(error, 'error');
});

// Handle success messages if needed (could be improved with custom HX-Trigger headers)
document.body.addEventListener('htmx:afterOnLoad', function (evt) {
    // Logic for success notifications could go here
});

// --- Confirmation Modal Logic ---
function askConfirmation(message) {
    return new Promise((resolve) => {
        const overlay = document.getElementById('modal-overlay');
        const confirmBtn = document.getElementById('modal-confirm');
        const cancelBtn = document.getElementById('modal-cancel');
        const messageElem = document.getElementById('modal-message');

        if (!overlay || !confirmBtn || !cancelBtn || !messageElem) {
            resolve(confirm(message));
            return;
        }

        messageElem.textContent = message;
        overlay.style.display = 'flex';

        confirmBtn.onclick = () => { overlay.style.display = 'none'; resolve(true); };
        cancelBtn.onclick = () => { overlay.style.display = 'none'; resolve(false); };
    });
}

// --- Notifications ---
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;
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

// --- Client-side dynamic lists (Recipes, Expense Items) ---
// These are kept for now as they are cleaner to manage on the client before submission.

// Recipe logic for products
window.currentRecipe = [];
window.addMaterialToProduct = function () {
    const select = document.getElementById('recipe-ingredient-select');
    const name = select.value;
    const qtyInput = document.getElementById('recipe-quantity');
    const quantity = parseFloat(qtyInput.value);

    if (!name || isNaN(quantity) || quantity <= 0) {
        showToast("Enter valid ingredient and quantity", "error");
        return;
    }

    const unit = select.selectedOptions[0]?.dataset.unit || '';
    window.currentRecipe.push({ name, quantity, unit });
    updateRecipeList();
    select.value = ""; qtyInput.value = "";
}

window.removeIngredientFromRecipe = function (index) {
    window.currentRecipe.splice(index, 1);
    updateRecipeList();
}

function updateRecipeList() {
    const list = document.getElementById('recipe-list');
    if (!list) return;
    list.innerHTML = '';
    window.currentRecipe.forEach((ing, index) => {
        const li = document.createElement('li');
        li.className = 'recipe-item';
        li.innerHTML = `
            <span><strong>${ing.name}</strong> - ${ing.quantity} ${ing.unit}</span>
            <button type="button" onclick="removeIngredientFromRecipe(${index})">×</button>
        `;
        list.appendChild(li);
    });
    const jsonInput = document.getElementById('recipe-json');
    if (jsonInput) jsonInput.value = JSON.stringify(window.currentRecipe);
}

// Expense Items logic
window.currentExpenseItems = [];
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

    window.currentExpenseItems.push({
        expense_type_id: parseInt(typeId),
        expense_type_name: typeName,
        quantity: quantity,
        unit_id: parseInt(unitId),
        unit_name: unitName,
        price_per_unit: price
    });

    updateExpenseItemsList();
    qtyInput.value = '';
    priceInput.value = '';
}

window.removeExpenseItemRow = function (index) {
    window.currentExpenseItems.splice(index, 1);
    updateExpenseItemsList();
}

function updateExpenseItemsList() {
    const list = document.getElementById('expense-items-list');
    if (!list) return;
    list.innerHTML = '';
    let total = 0;
    window.currentExpenseItems.forEach((item, index) => {
        const itemTotal = item.quantity * item.price_per_unit;
        total += itemTotal;
        const li = document.createElement('li');
        li.className = 'recipe-item';
        li.innerHTML = `
            <span><strong>${item.expense_type_name}</strong>: ${item.quantity} ${item.unit_name} x ${item.price_per_unit} = ${itemTotal.toFixed(2)}</span>
            <button type="button" onclick="removeExpenseItemRow(${index})">×</button>
            <input type="hidden" name="items[${index}][expense_type_id]" value="${item.expense_type_id}">
            <input type="hidden" name="items[${index}][quantity]" value="${item.quantity}">
            <input type="hidden" name="items[${index}][unit_id]" value="${item.unit_id}">
            <input type="hidden" name="items[${index}][price_per_unit]" value="${item.price_per_unit}">
        `;
        list.appendChild(li);
    });
    document.getElementById('expense-doc-total').innerText = total.toFixed(2);
}