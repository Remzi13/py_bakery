// POS Panel JavaScript

const CURRENCY = '₽';
let products = [];
let currentOrder = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    const searchInput = document.getElementById('product-search');
    const completeNowBtn = document.getElementById('complete-now-btn');
    const createOrderBtn = document.getElementById('create-order-btn');
    const clearBtn = document.getElementById('clear-order-btn');
    const orderForm = document.getElementById('order-form');

    searchInput.addEventListener('input', (e) => {
        filterProducts(e.target.value);
    });

    completeNowBtn.addEventListener('click', completeNow);
    createOrderBtn.addEventListener('click', openOrderModal);
    clearBtn.addEventListener('click', clearOrder);
    orderForm.addEventListener('submit', submitOrderForm);
}

// Load products from API
async function loadProducts() {
    try {
        const response = await fetch('/api/products/');
        if (!response.ok) throw new Error('Failed to load products');

        products = await response.json();
        renderProducts(products);
    } catch (error) {
        console.error('Error loading products:', error);
        showToast('Failed to load products', 'error');
        document.getElementById('products-grid').innerHTML =
            '<div class="loading-message" style="color: #fc8181;">Error loading products</div>';
    }
}

// Render products in grid
function renderProducts(productsToRender) {
    const grid = document.getElementById('products-grid');

    if (productsToRender.length === 0) {
        grid.innerHTML = '<div class="loading-message">No products found</div>';
        return;
    }

    grid.innerHTML = productsToRender.map(product => `
        <div class="product-card" onclick="addToOrder(${product.id})">
            <div class="product-name">${escapeHtml(product.name)}</div>
            <div class="product-price">${CURRENCY}${product.price.toFixed(2)}</div>
        </div>
    `).join('');
}

// Filter products based on search
function filterProducts(searchTerm) {
    const filtered = products.filter(product =>
        product.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    renderProducts(filtered);
}

// Add product to order
function addToOrder(productId) {
    const product = products.find(p => p.id === productId);
    if (!product) return;

    const existingItem = currentOrder.find(item => item.productId === productId);

    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        currentOrder.push({
            productId: product.id,
            name: product.name,
            price: product.price,
            quantity: 1
        });
    }

    renderOrder();
    showToast(`Added ${product.name}`, 'success');
}

// Remove item from order
function removeFromOrder(productId) {
    currentOrder = currentOrder.filter(item => item.productId !== productId);
    renderOrder();
    showToast('Item removed', 'info');
}

// Update item quantity
function updateQuantity(productId, change) {
    const item = currentOrder.find(item => item.productId === productId);
    if (!item) return;

    item.quantity += change;

    if (item.quantity <= 0) {
        removeFromOrder(productId);
    } else {
        renderOrder();
    }
}

// Render current order
function renderOrder() {
    const orderItemsContainer = document.getElementById('order-items');
    const completeNowBtn = document.getElementById('complete-now-btn');
    const createOrderBtn = document.getElementById('create-order-btn');
    const clearBtn = document.getElementById('clear-order-btn');

    if (currentOrder.length === 0) {
        orderItemsContainer.innerHTML = `
            <div class="empty-order">
                <p>No items in order</p>
                <p class="empty-order-hint">Click on products to add them</p>
            </div>
        `;
        completeNowBtn.disabled = true;
        createOrderBtn.disabled = true;
        clearBtn.style.display = 'none';
    } else {
        orderItemsContainer.innerHTML = currentOrder.map(item => {
            const itemTotal = item.price * item.quantity;
            return `
                <div class="order-item">
                    <div class="order-item-header">
                        <span class="order-item-name">${escapeHtml(item.name)}</span>
                        <button class="order-item-remove" onclick="removeFromOrder(${item.productId})">
                            Remove
                        </button>
                    </div>
                    <div class="order-item-controls">
                        <div class="quantity-controls">
                            <button class="qty-btn" onclick="updateQuantity(${item.productId}, -1)">−</button>
                            <span class="quantity-display">${item.quantity}</span>
                            <button class="qty-btn" onclick="updateQuantity(${item.productId}, 1)">+</button>
                        </div>
                        <span class="order-item-total">${CURRENCY}${itemTotal.toFixed(2)}</span>
                    </div>
                </div>
            `;
        }).join('');

        completeNowBtn.disabled = false;
        createOrderBtn.disabled = false;
        clearBtn.style.display = 'block';
    }

    updateOrderSummary();
}

// Update order summary (totals)
function updateOrderSummary() {
    const subtotal = currentOrder.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    const total = subtotal; // Can add tax/discount here if needed

    document.getElementById('order-subtotal').textContent = `${CURRENCY}${subtotal.toFixed(2)}`;
    document.getElementById('order-total').textContent = `${CURRENCY}${total.toFixed(2)}`;
    return subtotal;
}

// Complete order now (immediate sale)
async function completeNow() {
    if (currentOrder.length === 0) return;

    const completeNowBtn = document.getElementById('complete-now-btn');
    completeNowBtn.disabled = true;
    completeNowBtn.textContent = 'Processing...';

    try {
        const response = await fetch('/api/orders/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                items: currentOrder.map(item => ({
                    product_id: item.productId,
                    quantity: item.quantity
                })),
                complete_now: true
            })
        });

        if (!response.ok) {
            throw new Error('Failed to complete order');
        }

        const order = await response.json();
        showToast(`Order completed! Total: ${CURRENCY}${updateOrderSummary(true).toFixed(2)}`, 'success');
        clearOrder();
    } catch (error) {
        console.error('Error completing order:', error);
        showToast('Failed to complete order', 'error');
    } finally {
        completeNowBtn.disabled = false;
        completeNowBtn.textContent = '✓ Complete Now';
    }
}

// Open order modal
function openOrderModal() {
    if (currentOrder.length === 0) return;

    const modal = document.getElementById('order-modal');
    modal.style.display = 'flex';

    // Set minimum completion date to current time
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('completion-date').min = now.toISOString().slice(0, 16);
}

// Close order modal
function closeOrderModal() {
    const modal = document.getElementById('order-modal');
    modal.style.display = 'none';
    document.getElementById('order-form').reset();
}

// Submit order form
async function submitOrderForm(e) {
    e.preventDefault();

    if (currentOrder.length === 0) return;

    const formData = new FormData(e.target);
    const completionDate = formData.get('completion_date');
    const additionalInfo = formData.get('additional_info');

    try {
        const response = await fetch('/api/orders/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                items: currentOrder.map(item => ({
                    product_id: item.productId,
                    quantity: item.quantity
                })),
                completion_date: completionDate,
                additional_info: additionalInfo || null
            })
        });

        if (!response.ok) {
            throw new Error('Failed to create order');
        }

        const order = await response.json();
        showToast(`Order #${order.id} created successfully!`, 'success');
        closeOrderModal();
        clearOrder();
    } catch (error) {
        console.error('Error creating order:', error);
        showToast('Failed to create order', 'error');
    }
}

// Clear current order
function clearOrder() {
    if (currentOrder.length === 0) return;

    if (confirm('Clear all items from order?')) {
        currentOrder = [];
        renderOrder();
        showToast('Order cleared', 'info');
    }
}

// Toast notification system
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);

    // Trigger animation
    setTimeout(() => toast.classList.add('show'), 10);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Utility: Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
