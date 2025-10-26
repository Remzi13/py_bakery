from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout, 
    QLineEdit, QPushButton, QComboBox, QTableWidget, QTabWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QHeaderView, QDoubleSpinBox, QHBoxLayout,
    QDialog
)

import model.model as model

class AddIngredientsDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Добавить Ингредиент")
        self.model = model
        layout =  QGridLayout()

        self.name_input = QLineEdit()
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(model.get_units())

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.accept)

        layout.addWidget(QLabel("Название:"), 0, 0)
        layout.addWidget(self.name_input, 0, 1)
        layout.addWidget(QLabel("Ед. измерения:"), 1, 0)
        layout.addWidget(self.unit_combo, 1, 1)
        layout.addWidget(save_button, 2, 0, 1, 2)

        self.setLayout(layout)

    def accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название ингредиента.")
            return
        self.model.add_ingredient(self.name_input.text().strip(), self.unit_combo.currentIndex())
        return super().accept()

class IngredientsTab(QWidget):
    def __init__(self, model):
        super().__init__()
        
        self.model = model
        add_layout = QGridLayout()
        
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_ingredient)
        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_ingredient)
        self.del_button = QPushButton("Удалить")
        self.del_button.clicked.connect(self.del_ingredient)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Название", "Ед. изм."])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # выделение строк
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        add_layout.addWidget(self.add_button, 1, 0)
        add_layout.addWidget(self.edit_button, 1, 1)
        add_layout.addWidget(self.del_button, 1, 2)
        add_layout.addWidget(QLabel("Склад:"), 2, 0, 1, 3)
        add_layout.addWidget(self.table, 3, 0, 1, 3) 

        self.setLayout(add_layout)

        self.update_ingredients_table()

    def on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            ingredient_name = self.table.item(selected_row, 0).text()
            # Здесь можно добавить логику для обработки выбранного ингредиента
            print(f"Выбран ингредиент: {ingredient_name}")

    def add_ingredient(self):        

        dialog = AddIngredientsDialog(self.model)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Ошибка", "Введите название ингредиента.")
            return
                
        self.update_ingredients_table()

    def edit_ingredient(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите ингредиент для редактирования.")
            return

        selected_row = selected_rows[0].row()
        ingredient_name = self.table.item(selected_row, 0).text()
        ingredient = self.model.get_ingredient(ingredient_name)

        if not ingredient:
            QMessageBox.warning(self, "Ошибка", "Ингредиент не найден.")
            return

        dialog = AddIngredientsDialog(self.model)
        dialog.name_input.setText(ingredient.name())
        dialog.unit_combo.setCurrentIndex(ingredient.unit())

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return          

        # Удаляем старый ингредиент и добавляем новый с обновленными данными
        self.model.ingredients = [ing for ing in self.model.get_ingredients() if ing.name() != ingredient.name()]
        self.model.add_ingredient(dialog.name_input.text().strip(), dialog.unit_combo.currentIndex())

        self.update_ingredients_table()

    def del_ingredient(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите ингредиент для удаления.")
            return

        selected_row = selected_rows[0].row()
        ingredient_name = self.table.item(selected_row, 0).text()

        confirm = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить ингредиент '{ingredient_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.model.ingredients = [ing for ing in self.model.get_ingredients() if ing.name() != ingredient_name]
            self.update_ingredients_table()
        
    def update_ingredients_table(self):
        data = self.model.get_ingredients()
        self.table.clearContents()
        self.table.setRowCount(len(data))

        for i, row in enumerate(data):            
            self.table.setItem(i, 0, QTableWidgetItem(row.name()))
            self.table.setItem(i, 1, QTableWidgetItem(self.model.get_units()[row.unit()]))

class AddProductDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Добавить Продукт")
        self.model = model
        layout =  QGridLayout()

        self.name_input = QLineEdit()
        self.price_input = QDoubleSpinBox()        
        self.price_input.setRange(0.0, 1000.0)
        self.price_input.setDecimals(2)
        self.price_input.setSingleStep(0.1)

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

        ing_layout.addWidget(QLabel("Ингредиент:"))
        ing_layout.addWidget(self.ingredient_combo)
        ing_layout.addWidget(self.ing_quantity)
        ing_layout.addWidget(self.add_ingredient_button)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.accept)

        add_layout = QVBoxLayout()
        add_layout.addLayout(ing_layout)
        add_layout.addWidget(self.ing_table) 

        layout.addWidget(QLabel("Название:"), 0, 0)
        layout.addWidget(self.name_input, 0, 1)
        layout.addWidget(QLabel("Цена:"), 1, 0)
        layout.addWidget(self.price_input, 1, 1)
        layout.addLayout(add_layout, 2, 0, 1, 2)
        layout.addWidget(save_button, 3, 0, 1, 2)

        self.setLayout(layout)

    def add_ingredient(self):
        ingredient_name = self.ingredient_combo.currentText()
        quantity = self.ing_quantity.value()
        
        ing = self.model.get_ingredient(ingredient_name)

        row_position = self.ing_table.rowCount()
        self.ing_table.insertRow(row_position)
        self.ing_table.setItem(row_position, 0, QTableWidgetItem(ingredient_name))
        self.ing_table.setItem(row_position, 1, QTableWidgetItem(str(quantity)))
        self.ing_table.setItem(row_position, 2, QTableWidgetItem(self.model.get_units()[ing.unit()]))

    def accept(self):
        if not self.name_input.text().strip() or not self.price_input.value():
            QMessageBox.warning(self, "Ошибка", "Введите название и цену продукта.")
            return
        ingredients = []
        for row in range(self.ing_table.rowCount()):
            ing_name = self.ing_table.item(row, 0).text()
            quantity = float(self.ing_table.item(row, 1).text())
            ingredients.append({'name': ing_name, 'quantity': quantity})

        self.model.add_product(self.name_input.text().strip(), float(self.price_input.value()), ingredients)

        return super().accept()

class ProductsTab(QWidget):
    def __init__(self, model):
        super().__init__()

        self.model = model

        add_layout = QGridLayout()

        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_product)
        self.del_button = QPushButton("Удалить")
        self.del_button.clicked.connect(self.delete_product)
        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_product)

        self.products_tabel = QTableWidget()
        self.products_tabel.setColumnCount(2)
        self.products_tabel.setHorizontalHeaderLabels(["Назавание", "Цена"])
        self.products_tabel.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.products_tabel.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # выделение строк
        self.products_tabel.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.products_tabel.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_tabel.itemSelectionChanged.connect(self.on_selection_changed)

        add_layout.addWidget(self.add_button, 1, 0)  
        add_layout.addWidget(self.edit_button, 1, 1) 
        add_layout.addWidget(self.del_button, 1, 2) 
        add_layout.addWidget(self.products_tabel, 2, 0, 1, 3)  
    
        self.setLayout(add_layout)

        self.update_products_table()

    def on_selection_changed(self):
        selected_rows = self.products_tabel.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            product_name = self.products_tabel.item(selected_row, 0).text()
            # Здесь можно добавить логику для обработки выбранного продукта
            print(f"Выбран продукт: {product_name}")    

    def add_product(self):
        dialog = AddProductDialog(self.model)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.update_products_table()

    def edit_product(self):
        selected_rows = self.products_tabel.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите продукт для редактирования.")
            return

        selected_row = selected_rows[0].row()
        product_name = self.products_tabel.item(selected_row, 0).text()
        product = None
        for prod in self.model.get_products():
            if prod.name() == product_name:
                product = prod
                break

        if not product:
            QMessageBox.warning(self, "Ошибка", "Продукт не найден.")
            return

        dialog = AddProductDialog(self.model)
        dialog.name_input.setText(product.name())
        dialog.price_input.setValue(product.price())
        for ing in product.ingredients():
            row_position = dialog.ing_table.rowCount()
            dialog.ing_table.insertRow(row_position)
            dialog.ing_table.setItem(row_position, 0, QTableWidgetItem(ing['name']))
            dialog.ing_table.setItem(row_position, 1, QTableWidgetItem(str(ing['quantity'])))
            ing_obj = self.model.get_ingredient(ing['name'])
            dialog.ing_table.setItem(row_position, 2, QTableWidgetItem(self.model.get_units()[ing_obj.unit()]))

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return          

        # Удаляем старый продукт и добавляем новый с обновленными данными
        self.model.delete_product(product.name())
        ingredients = []
        for row in range(dialog.ing_table.rowCount()):
            ing_name = dialog.ing_table.item(row, 0).text()
            quantity = float(dialog.ing_table.item(row, 1).text())
            ingredients.append({'name': ing_name, 'quantity': quantity})

        self.model.add_product(dialog.name_input.text().strip(), float(dialog.price_input.value()), ingredients)

        self.update_products_table()    

    def delete_product(self):
        selected_rows = self.products_tabel.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите продукт для удаления.")
            return

        selected_row = selected_rows[0].row()
        product_name = self.products_tabel.item(selected_row, 0).text()

        confirm = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить продукт '{product_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self.model.delete_product(product_name)
            self.update_products_table()

    def update_products_table(self):
        data = self.model.get_products()
        self.products_tabel.clearContents()
        self.products_tabel.setRowCount(len(data))

        for i, row in enumerate(data):            
            self.products_tabel.setItem(i, 0, QTableWidgetItem(row.name()))
            self.products_tabel.setItem(i, 1, QTableWidgetItem(str(row.price())))  

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