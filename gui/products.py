from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout, 
    QLineEdit, QPushButton, QComboBox, QTableWidget, QTabWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QHeaderView, QDoubleSpinBox, QHBoxLayout
)

import model.model as model

class IngredientsTab(QWidget):
    def __init__(self, model):
        super().__init__()
        
        self.model = model
        add_layout = QGridLayout()

        self.name_input = QLineEdit()
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(model.get_units())
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_ingredient)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Название", "Ед. изм."])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        add_layout.addWidget(QLabel("Название:"), 0, 0)
        add_layout.addWidget(self.name_input, 0, 1)
        add_layout.addWidget(QLabel("Ед. измерения:"), 1, 0)
        add_layout.addWidget(self.unit_combo, 1, 1)
        add_layout.addWidget(self.add_button, 2, 0, 1, 2)
        add_layout.addWidget(QLabel("Склад:"), 3, 0, 1, 2)
        add_layout.addWidget(self.table, 4, 0, 1, 2) 

        self.setLayout(add_layout)

        self.update_ingredients_table()

    def add_ingredient(self):        

        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название ингредиента.")
            return
        
        self.model.add_ingredient(self.name_input.text().strip(), self.unit_combo.currentIndex())
        self.update_ingredients_table()

        # Очистить поля ввода
        self.name_input.clear()
        self.unit_combo.setCurrentIndex(0)

    def update_ingredients_table(self):
        data = self.model.get_ingredients()
        self.table.clearContents()
        self.table.setRowCount(len(data))

        for i, row in enumerate(data):            
            self.table.setItem(i, 0, QTableWidgetItem(row['name']))
            self.table.setItem(i, 1, QTableWidgetItem(self.model.get_units()[row['unit']]))


class ProductsTab(QWidget):
    def __init__(self, model):
        super().__init__()

        self.model = model
        add_layout = QGridLayout()

        self.name_input = QLineEdit()
        self.price_input = QDoubleSpinBox()        
        self.price_input.setRange(0.0, 1000.0)
        self.price_input.setDecimals(2)
        self.price_input.setSingleStep(0.1)

        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_product)

        ing_layout = QHBoxLayout()
        self.ingredient_combo = QComboBox()
        self.ingredient_combo.addItems(model.get_ingredients_names())
        self.ing_quantity = QDoubleSpinBox()
        self.ing_quantity.setRange(0.0, 10.0)
        self.ing_quantity.setDecimals(2)
        self.ing_quantity.setSingleStep(0.1)
        self.add_ingredient_button = QPushButton("+")
        self.add_ingredient_button.clicked.connect(self.add_ingredient)
        
        self.ing_table = QTableWidget()
        self.ing_table.setColumnCount(3)
        self.ing_table.setHorizontalHeaderLabels(["Ингредиент", "Количество", "Ед. изм."])
        self.ing_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        ing_layout.addWidget(QLabel("Ингредиент:"))
        ing_layout.addWidget(self.ingredient_combo)
        ing_layout.addWidget(self.ing_quantity)
        ing_layout.addWidget(self.add_ingredient_button)

        layout = QVBoxLayout()
        layout.addLayout(ing_layout)
        layout.addWidget(self.ing_table) 

        self.products_tabel = QTableWidget()
        self.products_tabel.setColumnCount(2)
        self.products_tabel.setHorizontalHeaderLabels(["Назавание", "Цена"])
        self.products_tabel.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        add_layout.addWidget(QLabel("Название:"), 0, 0)
        add_layout.addWidget(self.name_input, 0, 1)
        add_layout.addWidget(QLabel("Цена:"), 1, 0)
        add_layout.addWidget(self.price_input, 1, 1)                
        add_layout.addLayout(layout, 2, 0, 1, 2)
        add_layout.addWidget(self.add_button, 3, 0, 1, 3)  
        add_layout.addWidget(self.products_tabel, 4, 0, 1, 3)  
    
        self.setLayout(add_layout)

        self.update_products_table()

    def add_product(self):
        product_name = self.name_input.text().strip()
        product_price = self.price_input.value()
        if not product_name or not product_price:
            QMessageBox.warning(self, "Ошибка", "Введите название и цену продукта.")
            return

        ingredients = []
        for row in range(self.ing_table.rowCount()):
            ing_name = self.ing_table.item(row, 0).text()
            quantity = float(self.ing_table.item(row, 1).text())
            ingredients.append({'name': ing_name, 'quantity': quantity})

        self.model.add_product(product_name, float(product_price), ingredients) 

        self.update_products_table()

        self.name_input.clear()
        self.price_input.clear()        

    def add_ingredient(self):
        ingredient_name = self.ingredient_combo.currentText()
        quantity = self.ing_quantity.value()
        
        ing = self.model.get_ingredient(ingredient_name)

        row_position = self.ing_table.rowCount()
        self.ing_table.insertRow(row_position)
        self.ing_table.setItem(row_position, 0, QTableWidgetItem(ingredient_name))
        self.ing_table.setItem(row_position, 1, QTableWidgetItem(str(quantity)))
        self.ing_table.setItem(row_position, 2, QTableWidgetItem(self.model.get_units()[ing['unit']]))

    def update_products_table(self):
        data = self.model.get_products()
        self.products_tabel.clearContents()
        self.products_tabel.setRowCount(len(data))

        for i, row in enumerate(data):            
            self.products_tabel.setItem(i, 0, QTableWidgetItem(row['name']))
            self.products_tabel.setItem(i, 1, QTableWidgetItem(str(row['price'])))  

class ProductsWidget(QWidget):
    
    def __init__(self, model):
        super().__init__()        
        
        main_layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(IngredientsTab(model), "Ингредиенты")
        self.tab_widget.addTab(ProductsTab(model), "Продукция") 

        main_layout.addWidget(self.tab_widget)

        ## 2. Форма для добавления новой продукции
        #add_product_group = QGroupBox("2. Добавить новую продукцию")
        #add_layout = QGridLayout()
#
        #self.prod_name_input = QLineEdit()
        #self.prod_price_input = QLineEdit()
        #self.add_prod_button = QPushButton("Добавить Продукт")
        #self.add_prod_button.clicked.connect(self.add_new_product)
#
        #add_layout.addWidget(QLabel("Название:"), 0, 0)
        #add_layout.addWidget(self.prod_name_input, 0, 1)
        #add_layout.addWidget(QLabel("Цена (за шт.):"), 1, 0)
        #add_layout.addWidget(self.prod_price_input, 1, 1)
        #add_layout.addWidget(self.add_prod_button, 2, 0, 1, 2)
        #
        #add_product_group.setLayout(add_layout)
        #main_layout.addWidget(add_product_group)
        #
        ## 2. Форма для создания/редактирования рецепта
        #recipe_group = QGroupBox("2. Создать/Редактировать Рецепт")
        #recipe_layout = QGridLayout()
        #
        #self.product_select_combo = QComboBox() # Выбор продукта для рецепта
        #self.ingredient_for_recipe_combo = QComboBox() # Выбор ингредиента
        #self.quantity_needed_input = QLineEdit() # Количество ингредиента
        #self.add_recipe_button = QPushButton("Добавить Ингредиент в Рецепт")
        #self.add_recipe_button.clicked.connect(self.add_ingredient_to_recipe)
        #
        #self.recipe_table = QTableWidget()
        #self.recipe_table.setColumnCount(3)
        #self.recipe_table.setHorizontalHeaderLabels(["Ингредиент", "Количество", "Ед. изм."])
        #self.recipe_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
#
        #recipe_layout.addWidget(QLabel("Продукт:"), 0, 0)
        #recipe_layout.addWidget(self.product_select_combo, 0, 1)
        #recipe_layout.addWidget(QLabel("Ингредиент:"), 1, 0)
        #recipe_layout.addWidget(self.ingredient_for_recipe_combo, 1, 1)
        #recipe_layout.addWidget(QLabel("Нужно (доли):"), 2, 0)
        #recipe_layout.addWidget(self.quantity_needed_input, 2, 1)
        #recipe_layout.addWidget(self.add_recipe_button, 3, 0, 1, 2)
        #
        #recipe_layout.addWidget(QLabel("Состав Рецепта:"), 4, 0, 1, 2)
        #recipe_layout.addWidget(self.recipe_table, 5, 0, 1, 2)
        #
        #recipe_group.setLayout(recipe_layout)
        #main_layout.addWidget(recipe_group)
#
        self.setLayout(main_layout)

    def add_new_product(self):
        pass  # Логика добавления нового продукта в БД

    def add_ingredient_to_recipe(self):
        pass  # Логика добавления ингредиента в рецепт продукта