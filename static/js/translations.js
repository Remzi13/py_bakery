// Translations for English and Russian
const translations = {
    en: {
        // Common
        loading: "Loading...",
        noRecentActivity: "No recent activity",
        cancel: "Cancel",
        save: "Save",
        actions: "Actions",
        delete: "Delete",
        deleteConfirm: "Are you sure you want to delete this?",
        approve: "Approve",
        reject: "Reject",
        approveConfirm: "Are you sure you want to approve this?",
        rejectConfirm: "Are you sure you want to reject this?",
        confirm: "Confirm",
        cancel: "Cancel",
        discount: "Discount (%)",
        subtotal: "Subtotal",

        // Dashboard
        dashboard: "Dashboard",
        totalRevenue: "Total Revenue",
        monthlyRevenue: "Monthly Revenue",
        monthlyExpenses: "Monthly Expenses",
        vsLastMonth: "↑ 12% vs last month",
        vsLastWeek: "↑ 12% vs last week",
        lowStockItems: "Low Stock Items",
        itemsToRestock: "Items to restock",
        profitMargin: "Profit Margin",
        addSale: "➕ Add Sale",
        addOrder: "➕ Add Order",
        addExpense: "➕ Add Expense",
        salesTrendLastWeek: "Sales Trend (Last 7 Days)",
        recentActivity: "Recent Activity",

        // Navigation
        products: "Products",
        stock: "Stock",
        sales: "Sales",
        orders: "Orders",
        expenses: "Expenses",
        suppliers: "Suppliers",
        ingredients: "Ingredients",
        writeoffs: "Write-offs",
        reports: "Reports",
        documentation: "Documentation",

        // Orders
        orderId: "Order ID",
        created: "Created",
        completionDate: "Completion Date",
        status: "Status",
        items: "Items",
        pendingOrders: "Pending Orders",
        noPendingOrders: "No pending orders",
        completeOrder: "Complete",
        infoOrder: "Info",
        statusPending: "Pending",
        statusCompleted: "Completed",
        confirmCompleteOrder: "Are you sure you want to mark this order as completed? This will deduct ingredients from stock and create sale records.",
        additionalInfo: "Additional Info",
        orderDetails: "Order Details",

        // Products
        addProduct: "Add Product",
        searchProducts: "Search products...",
        productName: "Name",
        price: "Price",
        ingredientsList: "Ingredients",
        selectIngredient: "Select Ingredient...",
        addMaterial: "Add",
        recipe: "Recipe (Materials)",
        saveProduct: "Save Product",

        // Materials
        addMaterialButton: "Add Material",
        searchMaterials: "Search materials...",
        materialName: "Material Name",
        baseUnit: "Base Unit",
        saveIngredient: "Save Ingredient",

        // Stock
        addStockItem: "Add Stock Item",
        searchStock: "Search stock...",
        stockItemName: "Item Name",
        category: "Category",
        quantity: "Quantity",
        unit: "Unit",
        initialQuantity: "Initial Quantity",
        saveStockItem: "Add Item",

        // Sales
        newSale: "New Sale",
        searchSales: "Search sales...",
        date: "Date",
        product: "Product",
        selectProduct: "Select Product",
        quantityPcs: "Quantity (pcs)",
        discount: "Discount (%)",
        total: "Total",
        registerSale: "Register Sale",

        // Expenses
        addExpenseButton: "Add Expense",
        searchExpenses: "Search expenses...",
        expenseType: "Type",
        expenseCategory: "Category",
        amount: "Amount (₽)",
        supplier: "Supplier",
        optionalSupplier: "Supplier (Optional)",
        saveExpense: "Save Expense",
        newExpenseDocument: "New Expense Document",
        expenseDocumentDetails: "Expense Document Details",
        close: "Close",
        pricePerUnit: "Price/Unit",
        totalPrice: "Total Price",
        totalAmount: "Total Amount",
        noItems: "No items",

        // Suppliers
        addSupplier: "Add Supplier",
        editSupplier: "Edit Supplier",
        searchSuppliers: "Search suppliers...",
        companyName: "Company Name",
        contactPerson: "Contact Person",
        phone: "Phone",
        email: "Email",
        address: "Address",
        contact: "Contact",
        saveSupplier: "Save Supplier",
        selectSupplier: "Select Supplier",

        // Write-offs
        addWriteoff: "Add Write-off",
        searchWriteoffs: "Search write-offs...",
        itemType: "Item Type",
        selectItem: "Select Item",
        reason: "Reason",
        recordWriteoff: "Record Write-off",
        itemTypeProduct: "Product",
        itemTypeStock: "Stock Item",

        // Reports
        reportsTitle: "Business Reports",
        revenueVsExpenses: "Revenue vs Expenses",
        topProducts: "Top Selling Products",
        expenseBreakdown: "Expense Breakdown",
        netProfit: "Net Profit",
        totalRevenueReport: "Total Revenue",
        totalExpensesReport: "Total Expenses",
        avgOrderValue: "Avg Order Value",
        profitMarginReport: "Profit Margin",
        dailyRevenue: "Daily Revenue",
        monthlyRevenueReport: "Monthly Revenue",
        selectPeriod: "Select Period",
        last7Days: "Last 7 Days",
        last30Days: "Last 30 Days",
        thisMonth: "This Month",
        thisYear: "This Year",
        noDataToDisplay: "No data available for selected period",

        // Language Switch
        language: "Language",
        english: "English",
        russian: "Русский",
        backToHome: "Back to Home",
        expenseTypes: "Expense Types",
        searchExpenseTypes: "Search types...",
        allCategories: "All Categories",
        noItemsInDocument: "No items added yet",
        clickToAddItem: "Click on types from the left to add them",
        documentSavedSuccessfully: "Document saved successfully",
    },
    ru: {
        // Common
        loading: "Загрузка...",
        noRecentActivity: "Нет недавней деятельности",
        cancel: "Отмена",
        save: "Сохранить",
        actions: "Действия",
        delete: "Удалить",
        deleteConfirm: "Вы уверены, что хотите удалить этот товар?",
        approve: "Подтвердить",
        reject: "Отклонить",
        approveConfirm: "Вы уверены, что хотите подтвердить этот заказ?",
        rejectConfirm: "Вы уверены, что хотите отклонить этот заказ?",
        confirm: "Подтвердить",
        cancel: "Отменить",
        discount: "Скидка (%)",
        subtotal: "Подытог",

        // Dashboard
        dashboard: "Панель управления",
        totalRevenue: "Общие доходы",
        monthlyRevenue: "Доход за месяц",
        vsLastMonth: "↑ 12% по сравнению с прошлым месяцем",
        monthlyExpenses: "Расходы за месяц",
        itemsToRestock: "Товаров для пополнения",
        profitMargin: "Рентабельность",
        addSale: "➕ Добавить продажу",
        addOrder: "➕ Добавить заказ",
        addExpense: "➕ Добавить расход",
        salesTrendLastWeek: "Тренд продаж (последние 7 дней)",
        recentActivity: "Недавняя деятельность",

        // Navigation
        products: "Товары",
        stock: "Запасы",
        sales: "Продажи",
        orders: "Заказы",
        expenses: "Расходы",
        suppliers: "Поставщики",
        ingredients: "Ингредиенты",
        writeoffs: "Списания",
        reports: "Отчёты",
        documentation: "Документация",

        // Orders
        orderId: "ID Заказа",
        created: "Создан",
        completionDate: "Дата выполнения",
        status: "Статус",
        items: "Позиции",
        pendingOrders: "Ожидающие заказы",
        noPendingOrders: "Нет ожидающих заказов",
        completeOrder: "Выполнить",
        infoOrder: "Инфо",
        statusPending: "Ожидает",
        statusCompleted: "Выполнен",
        confirmCompleteOrder: "Вы уверены, что хотите отметить этот заказ как выполненный? Это приведет к списанию ингредиентов со склада и созданию записей о продажах.",
        additionalInfo: "Дополнительная информация",
        orderDetails: "Детали заказа",

        // Products
        addProduct: "Добавить товар",
        searchProducts: "Поиск товаров...",
        productName: "Название",
        price: "Цена",
        ingredientsList: "Ингредиенты",
        selectIngredient: "Выбрать ингредиент...",
        addMaterial: "Добавить",
        recipe: "Рецепт (Ингредиенты)",
        saveProduct: "Сохранить товар",

        // Materials
        addMaterialButton: "Добавить материал",
        searchMaterials: "Поиск материалов...",
        materialName: "Название материала",
        baseUnit: "Базовая единица",
        saveIngredient: "Сохранить ингредиент",

        // Stock
        addStockItem: "Добавить товар на складе",
        searchStock: "Поиск на складе...",
        stockItemName: "Название товара",
        category: "Категория",
        quantity: "Количество",
        unit: "Единица",
        initialQuantity: "Начальное количество",
        saveStockItem: "Добавить товар",

        // Sales
        newSale: "Новая продажа",
        searchSales: "Поиск продаж...",
        date: "Дата",
        product: "Товар",
        selectProduct: "Выбрать товар",
        quantityPcs: "Количество (шт)",
        discount: "Скидка (%)",
        total: "Итого",
        registerSale: "Зарегистрировать продажу",

        // Expenses
        addExpenseButton: "Добавить расход",
        searchExpenses: "Поиск расходов...",
        expenseType: "Тип",
        expenseCategory: "Категория",
        amount: "Сумма (₽)",
        supplier: "Поставщик",
        optionalSupplier: "Поставщик (необязательно)",
        saveExpense: "Сохранить расход",
        newExpenseDocument: "Новый расходный документ",
        expenseDocumentDetails: "Детали расходного документа",
        close: "Закрыть",
        pricePerUnit: "Цена/Ед",
        totalPrice: "Общая цена",
        totalAmount: "Общая сумма",
        noItems: "Нет позиций",

        // Suppliers
        addSupplier: "Добавить поставщика",
        editSupplier: "Редактировать поставщика",
        searchSuppliers: "Поиск поставщиков...",
        companyName: "Название компании",
        contactPerson: "Контактное лицо",
        phone: "Телефон",
        email: "Email",
        address: "Адрес",
        contact: "Контакт",
        saveSupplier: "Сохранить поставщика",
        selectSupplier: "Выбрать поставщика",

        // Write-offs
        addWriteoff: "Добавить списание",
        searchWriteoffs: "Поиск списаний...",
        itemType: "Тип товара",
        selectItem: "Выбрать товар",
        reason: "Причина",
        recordWriteoff: "Зарегистрировать списание",
        itemTypeProduct: "Товар",
        itemTypeStock: "Товар на складе",

        // Reports
        reportsTitle: "Бизнес-отчёты",
        revenueVsExpenses: "Доходы vs Расходы",
        topProducts: "Популярные товары",
        expenseBreakdown: "Структура расходов",
        netProfit: "Чистая прибыль",
        totalRevenueReport: "Общий доход",
        totalExpensesReport: "Общие расходы",
        avgOrderValue: "Средний чек",
        profitMarginReport: "Рентабельность",
        dailyRevenue: "Дневная выручка",
        monthlyRevenueReport: "Месячная выручка",
        selectPeriod: "Выберите период",
        last7Days: "Последние 7 дней",
        last30Days: "Последние 30 дней",
        thisMonth: "Этот месяц",
        thisYear: "Этот год",
        noDataToDisplay: "Нет данных для отображения за выбранный период",

        // Language Switch
        language: "Язык",
        english: "English",
        russian: "Русский",
        backToHome: "На главную",
        expenseTypes: "Типы расходов",
        searchExpenseTypes: "Поиск типов...",
        allCategories: "Все категории",
        noItemsInDocument: "Позиции еще не добавлены",
        clickToAddItem: "Нажмите на типы слева, чтобы добавить их",
        documentSavedSuccessfully: "Документ успешно сохранен",
    }
};

// Current language
let currentLanguage = localStorage.getItem('language') || 'en';

// Get translation
function t(key) {
    return translations[currentLanguage][key] || translations['en'][key] || key;
}

// Switch language
function switchLanguage(lang) {
    if (translations[lang]) {
        currentLanguage = lang;
        localStorage.setItem('language', lang);
        updatePageLanguage();
        updateLanguageButtons();
    }
}

// Update language button styling
function updateLanguageButtons() {
    document.getElementById('lang-en')?.classList.toggle('active', currentLanguage === 'en');
    document.getElementById('lang-ru')?.classList.toggle('active', currentLanguage === 'ru');
}

// Update all translatable elements on the page
function updatePageLanguage() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            if (el.placeholder) el.placeholder = t(key);
        } else if (el.tagName === 'OPTION') {
            el.textContent = t(key);
        } else {
            el.textContent = t(key);
        }
    });

    // Update page title
    const activeTab = document.querySelector('.nav-btn.active');
    if (activeTab) {
        document.getElementById('page-title').innerText = t(activeTab.getAttribute('data-i18n') || activeTab.innerText);
    }

    // Update html lang attribute
    document.documentElement.lang = currentLanguage;
}

// Initialize translations on page load
document.addEventListener('DOMContentLoaded', () => {
    updatePageLanguage();
    updateLanguageButtons();
});

// Re-apply translations after HTMX content is loaded and settled
document.addEventListener('htmx:afterSettle', () => {
    updatePageLanguage();
});
