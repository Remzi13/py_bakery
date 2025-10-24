# main_app.py
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, 
    QWidget, QVBoxLayout, QLabel, QGridLayout, 
    QLineEdit, QPushButton, QComboBox, QTableWidget, 
    QTableWidgetItem, QMessageBox, QGroupBox, QHBoxLayout,
    QHeaderView
)
from PyQt6.QtCore import Qt
from db_connector import DBConnector # Импортируем наш класс для работы с БД
from datetime import datetime


# --- Вкладки (Просто заглушки пока) ---

class IngredientsTab(QWidget):
    """Вкладка для управления ингредиентами и остатками."""
    def __init__(self, db_connector):
        super().__init__()
        self.db = db_connector
        
        main_layout = QVBoxLayout()
        
        # 1. Форма для добавления нового ингредиента
        add_group = QGroupBox("1. Добавить новый ингредиент")
        add_layout = QGridLayout()

        self.name_input = QLineEdit()
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(['кг', 'грамм', 'литр', 'штуки'])
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_new_ingredient)

        add_layout.addWidget(QLabel("Название:"), 0, 0)
        add_layout.addWidget(self.name_input, 0, 1)
        add_layout.addWidget(QLabel("Ед. измерения:"), 1, 0)
        add_layout.addWidget(self.unit_combo, 1, 1)
        add_layout.addWidget(self.add_button, 2, 0, 1, 2)
        
        add_group.setLayout(add_layout)

        # 2. Форма для регистрации закупки (пополнение склада)
        purchase_group = QGroupBox("2. Закупка (Пополнение склада)")
        purchase_layout = QGridLayout()
        
        # QComboBox для выбора существующего ингредиента
        self.ingredient_select_combo = QComboBox() 
        self.purchase_quantity_input = QLineEdit()
        self.purchase_price_input = QLineEdit()
        self.purchase_button = QPushButton("Зарегистрировать закупку")
        self.purchase_button.clicked.connect(self.register_purchase)

        purchase_layout.addWidget(QLabel("Ингредиент:"), 0, 0)
        purchase_layout.addWidget(self.ingredient_select_combo, 0, 1)
        purchase_layout.addWidget(QLabel("Количество:"), 1, 0)
        purchase_layout.addWidget(self.purchase_quantity_input, 1, 1)
        purchase_layout.addWidget(QLabel("Цена за ед.:"), 2, 0)
        purchase_layout.addWidget(self.purchase_price_input, 2, 1)
        purchase_layout.addWidget(self.purchase_button, 3, 0, 1, 2)

        purchase_group.setLayout(purchase_layout)

        # Компоновка форм добавления и закупки рядом
        form_layout = QHBoxLayout()
        form_layout.addWidget(add_group)
        form_layout.addWidget(purchase_group)
        
        # 3. Таблица для отображения остатков
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(4)
        self.stock_table.setHorizontalHeaderLabels(["ID", "Название", "Остаток", "Ед. изм."])
        # Растягиваем колонку "Название"
        self.stock_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        main_layout.addLayout(form_layout)
        main_layout.addWidget(QLabel("<h3>Текущие остатки на складе:</h3>"))
        main_layout.addWidget(self.stock_table)

        self.setLayout(main_layout)
        
        # Загрузка данных при старте
        self.load_ingredients_data()

    def load_ingredients_data(self):
        """Загружает список ингредиентов и обновляет таблицу/комбобоксы."""
        query = "SELECT ingredient_id, name, current_stock, unit_of_measure FROM Ingredients ORDER BY name"
        results = self.db.execute_query(query, fetch=True)
        
        if results is None:
            QMessageBox.critical(self, "Ошибка БД", "Не удалось загрузить данные об ингредиентах.")
            return

        # Обновление таблицы остатков
        self.stock_table.setRowCount(len(results))
        self.ingredient_select_combo.clear() # Очистка комбобокса перед заполнением

        for row_idx, row_data in enumerate(results):
            # Заполнение таблицы
            for col_idx, item in enumerate(row_data):
                cell = QTableWidgetItem(str(item))
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable) # Сделать нередактируемым
                self.stock_table.setItem(row_idx, col_idx, cell)
            
            # Заполнение комбобокса для закупки (сохраняем ID)
            self.ingredient_select_combo.addItem(row_data[1], row_data[0])

    def add_new_ingredient(self):
        """Добавляет новый ингредиент в базу данных."""
        name = self.name_input.text().strip()
        unit = self.unit_combo.currentText()
        
        if not name:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите название ингредиента.")
            return

        # Запрос на вставку (начальный остаток всегда 0)
        query = "INSERT INTO Ingredients (name, unit_of_measure, current_stock) VALUES (%s, %s, 0.000)"
        params = (name, unit)
        
        if self.db.execute_query(query, params):
            QMessageBox.information(self, "Успех", f"Ингредиент '{name}' успешно добавлен.")
            self.name_input.clear()
            self.load_ingredients_data() # Перезагрузка данных
        else:
            # Тут может быть ошибка UNIQUE KEY, если ингредиент уже есть
            QMessageBox.critical(self, "Ошибка", "Не удалось добавить ингредиент. Возможно, он уже существует.")

    def register_purchase(self):
        """Регистрирует закупку ингредиента и обновляет остаток."""
        ingredient_id = self.ingredient_select_combo.currentData()
        quantity_str = self.purchase_quantity_input.text().replace(',', '.')
        price_str = self.purchase_price_input.text().replace(',', '.')
        
        if not ingredient_id:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите ингредиент.")
            return
        
        try:
            quantity = float(quantity_str)
            price = float(price_str)
            if quantity <= 0 or price <= 0:
                 raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Внимание", "Количество и Цена должны быть положительными числами.")
            return
        
        total_cost = quantity * price
        
        # --- ИСПРАВЛЕНИЕ ДЛЯ ДАТЫ И SQLite ---
        # 1. Запрос на обновление остатка на складе (UPDATE Ingredients)
        update_query = "UPDATE Ingredients SET current_stock = current_stock + %s WHERE ingredient_id = %s"
        update_params = (quantity, ingredient_id)
        
        # 2. Запись в журнал закупок (INSERT Ingredient_Purchases)
        # Явно получаем текущее время в формате строки
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        insert_query = """
        INSERT INTO Ingredient_Purchases 
        (ingredient_id, purchase_date, quantity_bought, price_per_unit, total_cost) 
        VALUES (%s, %s, %s, %s, %s)
        """
        # Передаем дату как параметр!
        insert_params = (ingredient_id, current_date, quantity, price, total_cost)
        
        # Выполняем оба запроса
        # NOTE: В SQLite (как и в MySQL) мы полагаемся на успех выполнения каждого шага.
        update_success = self.db.execute_query(update_query, update_params)
        insert_success = self.db.execute_query(insert_query, insert_params)

        if update_success and insert_success:
            QMessageBox.information(self, "Успех", f"Закупка зарегистрирована. Остаток обновлен на {quantity}.")
            self.purchase_quantity_input.clear()
            self.purchase_price_input.clear()
            self.load_ingredients_data() # Перезагрузка данных
        else:
            # Если произошла ошибка, выводим общее сообщение.
            # (Для реальных приложений здесь нужна более сложная логика отката/транзакций)
            QMessageBox.critical(self, "Ошибка", "Не удалось зарегистрировать закупку. Проверьте консоль на ошибки БД.")

class ProductsTab(QWidget):
    """Вкладка для управления продукцией и рецептами."""
    def __init__(self, db_connector):
        super().__init__()
        self.db = db_connector
        
        main_layout = QVBoxLayout()
        
        # 1. Форма для добавления новой продукции
        add_product_group = QGroupBox("1. Добавить новую продукцию")
        add_layout = QGridLayout()

        self.prod_name_input = QLineEdit()
        self.prod_price_input = QLineEdit()
        self.add_prod_button = QPushButton("Добавить Продукт")
        self.add_prod_button.clicked.connect(self.add_new_product)

        add_layout.addWidget(QLabel("Название:"), 0, 0)
        add_layout.addWidget(self.prod_name_input, 0, 1)
        add_layout.addWidget(QLabel("Цена (за шт.):"), 1, 0)
        add_layout.addWidget(self.prod_price_input, 1, 1)
        add_layout.addWidget(self.add_prod_button, 2, 0, 1, 2)
        
        add_product_group.setLayout(add_layout)
        main_layout.addWidget(add_product_group)
        
        # 2. Форма для создания/редактирования рецепта
        recipe_group = QGroupBox("2. Создать/Редактировать Рецепт")
        recipe_layout = QGridLayout()
        
        self.product_select_combo = QComboBox() # Выбор продукта для рецепта
        self.ingredient_for_recipe_combo = QComboBox() # Выбор ингредиента
        self.quantity_needed_input = QLineEdit() # Количество ингредиента
        self.add_recipe_button = QPushButton("Добавить Ингредиент в Рецепт")
        self.add_recipe_button.clicked.connect(self.add_ingredient_to_recipe)
        
        self.recipe_table = QTableWidget()
        self.recipe_table.setColumnCount(3)
        self.recipe_table.setHorizontalHeaderLabels(["Ингредиент", "Количество", "Ед. изм."])
        self.recipe_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        recipe_layout.addWidget(QLabel("Продукт:"), 0, 0)
        recipe_layout.addWidget(self.product_select_combo, 0, 1)
        recipe_layout.addWidget(QLabel("Ингредиент:"), 1, 0)
        recipe_layout.addWidget(self.ingredient_for_recipe_combo, 1, 1)
        recipe_layout.addWidget(QLabel("Нужно (доли):"), 2, 0)
        recipe_layout.addWidget(self.quantity_needed_input, 2, 1)
        recipe_layout.addWidget(self.add_recipe_button, 3, 0, 1, 2)
        
        recipe_layout.addWidget(QLabel("Состав Рецепта:"), 4, 0, 1, 2)
        recipe_layout.addWidget(self.recipe_table, 5, 0, 1, 2)
        
        recipe_group.setLayout(recipe_layout)
        main_layout.addWidget(recipe_group)

        # Сигнал: при смене продукта в комбобоксе, обновляем таблицу рецепта
        self.product_select_combo.currentIndexChanged.connect(self.load_recipe_details)

        self.setLayout(main_layout)
        
        # Загрузка данных при старте
        self.load_all_data()
        
    def load_all_data(self):
        """Загружает список продукции и ингредиентов для комбобоксов."""
        
        # 1. Загрузка продукции для комбобокса (для рецепта)
        products_query = "SELECT product_id, name FROM Products ORDER BY name"
        products = self.db.execute_query(products_query, fetch=True)
        self.product_select_combo.clear()
        if products:
            for prod_id, name in products:
                self.product_select_combo.addItem(name, prod_id)
        
        # 2. Загрузка ингредиентов для комбобокса (для рецепта)
        ingredients_query = "SELECT ingredient_id, name, unit_of_measure FROM Ingredients ORDER BY name"
        self.ingredients_data = self.db.execute_query(ingredients_query, fetch=True)
        self.ingredient_for_recipe_combo.clear()
        if self.ingredients_data:
            for ing_id, name, unit in self.ingredients_data:
                # Храним ID ингредиента и его Ед. изм. в Data
                self.ingredient_for_recipe_combo.addItem(f"{name} ({unit})", (ing_id, unit)) 
                
        self.load_recipe_details() # Загрузить рецепт первого продукта по умолчанию

    def add_new_product(self):
        """Добавляет новый продукт в таблицу Products."""
        name = self.prod_name_input.text().strip()
        price_str = self.prod_price_input.text().replace(',', '.')
        
        if not name or not price_str:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, заполните все поля.")
            return

        try:
            price = float(price_str)
            if price < 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Внимание", "Цена должна быть положительным числом.")
            return

        query = "INSERT INTO Products (name, selling_price, unit_of_measure) VALUES (%s, %s, 'штуки')"
        params = (name, price)
        
        if self.db.execute_query(query, params):
            QMessageBox.information(self, "Успех", f"Продукт '{name}' успешно добавлен.")
            self.prod_name_input.clear()
            self.prod_price_input.clear()
            self.load_all_data() # Перезагрузка списка продуктов
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось добавить продукт. Возможно, он уже существует.")

    def load_recipe_details(self):
        """Загружает и отображает состав рецепта для выбранного продукта."""
        product_id = self.product_select_combo.currentData()
        if not product_id:
            self.recipe_table.setRowCount(0)
            return

        query = """
        SELECT i.name, r.quantity_needed, i.unit_of_measure 
        FROM Recipe r
        JOIN Ingredients i ON r.ingredient_id = i.ingredient_id
        WHERE r.product_id = %s
        """
        results = self.db.execute_query(query, (product_id,), fetch=True)
        
        self.recipe_table.setRowCount(0) # Очищаем таблицу
        if results is None: return

        self.recipe_table.setRowCount(len(results))
        for row_idx, row_data in enumerate(results):
            for col_idx, item in enumerate(row_data):
                cell = QTableWidgetItem(str(item))
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable) 
                self.recipe_table.setItem(row_idx, col_idx, cell)

    def add_ingredient_to_recipe(self):
        """Добавляет или обновляет ингредиент в рецепте выбранного продукта (Исправлено для SQLite)."""
        product_id = self.product_select_combo.currentData()
        ingredient_data = self.ingredient_for_recipe_combo.currentData()
        quantity_str = self.quantity_needed_input.text().replace(',', '.')
        
        if not product_id or not ingredient_data:
            QMessageBox.warning(self, "Внимание", "Сначала добавьте продукты и ингредиенты.")
            return

        try:
            quantity = float(quantity_str)
            if quantity <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Внимание", "Количество должно быть положительным числом (можно доли).")
            return
        
        ingredient_id = ingredient_data[0]

        # --- ИСПРАВЛЕННАЯ ЛОГИКА ДЛЯ SQLite (UPDATE ИЛИ INSERT) ---
        
        # 1. Попытка ОБНОВИТЬ существующую запись
        update_query = """
        UPDATE Recipe 
        SET quantity_needed = %s
        WHERE product_id = %s AND ingredient_id = %s
        """
        update_params = (quantity, product_id, ingredient_id)
        
        # NOTE: execute_query вернет True, даже если запись не была найдена/обновлена,
        # так как это не ошибка синтаксиса.
        update_result = self.db.execute_query(update_query, update_params)

        # Проверка, была ли обновлена существующая запись.
        # В SQLite нет прямого способа получить количество затронутых строк через execute_query,
        # как мы его реализовали. Самый надежный способ - проверить, существует ли запись
        # перед UPDATE или использовать REPLACE INTO (но это сложнее для foreign keys).
        
        # Проверим, существует ли запись, чтобы решить: UPDATE или INSERT
        check_query = "SELECT COUNT(*) FROM Recipe WHERE product_id = %s AND ingredient_id = %s"
        count_result = self.db.execute_query(check_query, (product_id, ingredient_id), fetch=True)
        record_exists = count_result and count_result[0][0] > 0

        if record_exists:
            # Выполняем UPDATE, если запись существует
            if update_result:
                 QMessageBox.information(self, "Успех", "Количество ингредиента в рецепте успешно обновлено.")
            else:
                 QMessageBox.critical(self, "Ошибка", "Не удалось обновить рецепт.")
        else:
            # 2. Если запись НЕ существует, выполняем INSERT
            insert_query = """
            INSERT INTO Recipe (product_id, ingredient_id, quantity_needed)
            VALUES (%s, %s, %s)
            """
            insert_params = (product_id, ingredient_id, quantity)
            
            if self.db.execute_query(insert_query, insert_params):
                QMessageBox.information(self, "Успех", "Ингредиент успешно добавлен в рецепт.")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить ингредиент в рецепт.")

        # --- Общая очистка и обновление ---
        self.quantity_needed_input.clear()
        self.load_recipe_details() # Обновляем отображение рецепта

class SalesTab(QWidget):
    """Вкладка для регистрации продаж и списаний."""
    def __init__(self, db_connector):
        super().__init__()
        self.db = db_connector
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Регистрация Продаж и Списаний"))
        layout.addWidget(QLabel("Здесь будет форма для регистрации продажи/списания и журнал"))
        self.setLayout(layout)

class ExpensesTab(QWidget):
    """Вкладка для учета прочих расходов."""
    def __init__(self, db_connector):
        super().__init__()
        self.db = db_connector
        
        main_layout = QVBoxLayout()
        
        # 1. Форма добавления расхода
        add_expense_group = QGroupBox("Регистрация Прочего Расхода")
        add_layout = QGridLayout()

        self.date_input = QLineEdit() # Можно заменить на QDateEdit для удобства, но для простоты оставим LineEdit
        self.date_input.setText("YYYY-MM-DD") # Подсказка формата
        self.amount_input = QLineEdit()
        self.comment_input = QLineEdit()
        self.add_expense_button = QPushButton("Зарегистрировать Расход")
        self.add_expense_button.clicked.connect(self.add_new_expense)

        add_layout.addWidget(QLabel("Дата (YYYY-MM-DD):"), 0, 0)
        add_layout.addWidget(self.date_input, 0, 1)
        add_layout.addWidget(QLabel("Сумма ($):"), 1, 0)
        add_layout.addWidget(self.amount_input, 1, 1)
        add_layout.addWidget(QLabel("Комментарий:"), 2, 0)
        add_layout.addWidget(self.comment_input, 2, 1)
        add_layout.addWidget(self.add_expense_button, 3, 0, 1, 2)
        
        add_expense_group.setLayout(add_layout)
        
        # 2. Таблица журнала расходов
        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(3)
        self.expense_table.setHorizontalHeaderLabels(["Дата", "Сумма", "Комментарий"])
        self.expense_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        main_layout.addWidget(add_expense_group)
        main_layout.addWidget(QLabel("<h3>Журнал Расходов:</h3>"))
        main_layout.addWidget(self.expense_table)

        self.setLayout(main_layout)
        
        self.load_expenses_data()

    def load_expenses_data(self):
        """Загружает журнал расходов."""
        query = "SELECT expense_date, amount, comment FROM Expenses ORDER BY expense_date DESC LIMIT 50"
        results = self.db.execute_query(query, fetch=True)
        
        self.expense_table.setRowCount(0)
        if results:
            self.expense_table.setRowCount(len(results))
            for row_idx, row_data in enumerate(results):
                # Форматируем сумму
                row_data = list(row_data)
                row_data[1] = f"{row_data[1]:.2f}"
                
                for col_idx, item in enumerate(row_data):
                    cell = QTableWidgetItem(str(item))
                    cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable) 
                    self.expense_table.setItem(row_idx, col_idx, cell)

    def add_new_expense(self):
        """Добавляет новый расход в базу данных."""
        date_str = self.date_input.text().strip()
        amount_str = self.amount_input.text().replace(',', '.')
        comment = self.comment_input.text().strip()
        
        if not date_str or not amount_str:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, заполните поля Дата и Сумма.")
            return

        try:
            amount = float(amount_str)
            if amount <= 0: raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Внимание", "Сумма должна быть положительным числом.")
            return

        # Простая проверка формата даты (можно улучшить)
        if len(date_str) != 10 or date_str[4] != '-' or date_str[7] != '-':
            QMessageBox.warning(self, "Внимание", "Дата должна быть в формате YYYY-MM-DD.")
            return

        query = "INSERT INTO Expenses (expense_date, amount, comment) VALUES (%s, %s, %s)"
        params = (date_str, amount, comment)
        
        if self.db.execute_query(query, params):
            QMessageBox.information(self, "Успех", f"Расход {amount:.2f} успешно зарегистрирован.")
            self.amount_input.clear()
            self.comment_input.clear()
            # self.date_input.setText("YYYY-MM-DD") # Можно очистить или оставить
            self.load_expenses_data() # Перезагрузка данных
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось зарегистрировать расход.")


# --- Главное окно ---

class BakeryApp(QMainWindow):
    """Основное окно приложения."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Партнер Программиста: Управление Пекарней")
        self.setGeometry(100, 100, 800, 600)

        # 1. Подключение к базе данных
        self.db = DBConnector()
        self.db.connect()

        # 2. Создание главного виджета с вкладками
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        # 3. Добавление вкладок
        self.tab_widget.addTab(IngredientsTab(self.db), "1. Ингредиенты (Склад)")
        self.tab_widget.addTab(ProductsTab(self.db), "2. Продукция (Рецепты)")
        self.tab_widget.addTab(SalesTab(self.db), "3. Продажи и Списания")
        self.tab_widget.addTab(ExpensesTab(self.db), "4. Расходы")
        
    def closeEvent(self, event):
        """Обработка закрытия приложения для отключения от БД."""
        self.db.disconnect()
        super().closeEvent(event)


if __name__ == '__main__':
    if DB_USER == 'your_mysql_user' or DB_PASSWORD == 'your_mysql_password':
        print("-" * 50)
        print("!!! ВНИМАНИЕ !!!")
        print("Пожалуйста, замените DB_USER и DB_PASSWORD в main_app.py на свои учетные данные.")
        print("-" * 50)
    
    app = QApplication(sys.argv)
    window = BakeryApp()
    window.show()
    sys.exit(app.exec())