from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGridLayout, 
    QLineEdit, QPushButton, QComboBox, QTableWidget, QTabWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QHeaderView, QDoubleSpinBox, QHBoxLayout,
    QDialog
)

import model.entities as entities

class AddIngredientsDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Ингредиент")
        self._model = model
        layout =  QGridLayout()

        self.name_input = QLineEdit()
        self.unit_combo = QComboBox()        
        self.unit_combo.addItems(list(entities.UNIT_NAMES.values()))

        save_button = QPushButton("Добавить")
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
        name = self.name_input.text().strip()
        if self._model.ingredients().has(name):
            QMessageBox.warning(self, "Ошибка", "Введите название ингредиента который уже сушествует.")
            return
        self._model.ingredients().add(self.name_input.text().strip(), entities.unit_by_name(self.unit_combo.currentText()))
        return super().accept()

class IngredientsTab(QWidget):
    def __init__(self, model):
        super().__init__()
        
        self._model = model
        add_layout = QGridLayout()
        
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_ingredient)        
        self.del_button = QPushButton("Удалить")
        self.del_button.clicked.connect(self.del_ingredient)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Название", "Ед. изм."])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        add_layout.addWidget(self.add_button, 1, 0)        
        add_layout.addWidget(self.del_button, 1, 1)
        add_layout.addWidget(QLabel("Склад:"), 2, 0, 1, 2)
        add_layout.addWidget(self.table, 2, 0, 1, 2) 

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

        dialog = AddIngredientsDialog(self._model)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
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
            if self._model.ingredients().can_delete(ingredient_name):
                self._model.ingredients().delete(ingredient_name)
                self.update_ingredients_table()
            else:
                QMessageBox.warning(self, "Ошибка", f"Нельзя удалить '{ingredient_name}' испльзуется в товаха.")
        
    def update_ingredients_table(self):
        data = self._model.ingredients().data()
        self.table.clearContents()
        self.table.setRowCount(len(data))

        for i, row in enumerate(data):            
            self.table.setItem(i, 0, QTableWidgetItem(row.name))
            self.table.setItem(i, 1, QTableWidgetItem(entities.UNIT_NAMES[row.unit]))

class CreateProductDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Новый продукт")
        self._model = model
        layout =  QGridLayout()

        self.name_input = QLineEdit()
        self.price_input = QDoubleSpinBox()        
        self.price_input.setRange(0.0, 10000.0)
        self.price_input.setDecimals(2)
        self.price_input.setSingleStep(0.1)
        
        ing_layout = QGridLayout()
        self.ingredient_combo = QComboBox()
        self.ingredient_combo.addItems(model.ingredients().names())
        self.ingredient_combo.currentIndexChanged.connect(self.ing_combo_changed)
        self.ing_quantity = QDoubleSpinBox()
        self.ing_quantity.setRange(0.0, 10.0)
        self.ing_quantity.setDecimals(2)
        self.ing_quantity.setSingleStep(0.1)
        self.add_ingredient_button = QPushButton("+")
        self.add_ingredient_button.clicked.connect(self.add_ingredient)
        self.del_ingredient_button = QPushButton("-")
        self.del_ingredient_button.clicked.connect(self.del_ingredient)
        ing = self._model.ingredients().by_name(model.ingredients().names()[0])        
        self.ing_unit = QLabel(entities.UNIT_NAMES[ing.unit])
                
        
        ing_layout.addWidget(QLabel("Ингредиент:"), 0, 0)
        ing_layout.addWidget(self.ingredient_combo, 0, 1)
        ing_layout.addWidget(self.ing_quantity, 0, 2)
        ing_layout.addWidget(self.ing_unit, 0, 3)
        ing_layout.addWidget(self.add_ingredient_button, 1, 0, 1, 2)
        ing_layout.addWidget(self.del_ingredient_button, 1, 2, 1, 2)

        self.ing_table = QTableWidget()
        self.ing_table.setColumnCount(3)
        self.ing_table.setHorizontalHeaderLabels(["Ингредиент", "Количество", "Ед. изм."])
        self.ing_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ing_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.ing_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.ing_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

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

    def ing_combo_changed(self):
        name = self.ingredient_combo.currentText()
        ing = self._model.ingredients().by_name(name)
        entities.UNIT_NAMES[ing.unit]
        self.ing_unit.setText(entities.UNIT_NAMES[ing.unit])

    def add_ingredient(self):
        ingredient_name = self.ingredient_combo.currentText()

        for row in range(self.ing_table.rowCount()):
            if self.ing_table.item(row, 0).text() == ingredient_name:        
                QMessageBox.warning(self, "Ошибка", "Продукт с таким именм уже добавлен.")
                return        
        
        quantity = self.ing_quantity.value()
        if not quantity > 0.0:
            QMessageBox.warning(self, "Ошибка", "Игредиент должен быть больше нуля.")
            return

        ing = self._model.ingredients().by_name(ingredient_name)

        row_position = self.ing_table.rowCount()
        self.ing_table.insertRow(row_position)
        self.ing_table.setItem(row_position, 0, QTableWidgetItem(ingredient_name))
        self.ing_table.setItem(row_position, 1, QTableWidgetItem(str(round(quantity, 3))))
        self.ing_table.setItem(row_position, 2, QTableWidgetItem(entities.UNIT_NAMES[ing.unit]))
    
    def del_ingredient(self):
        row = self.ing_table.currentRow()
        if row >= 0:
            self.ing_table.removeRow(row)

    def accept(self):
        name = self.name_input.text().strip()
        if not name or not self.price_input.value():
            QMessageBox.warning(self, "Ошибка", "Введите название и цену продукта.")
            return
        
        if self._model.products().has(name) is True:
            QMessageBox.warning(self, "Ошибка", "Продукт с таким именм уже сушествует.")
            return        
        
        ingredients = []
        for row in range(self.ing_table.rowCount()):
            ing_name = self.ing_table.item(row, 0).text()
            quantity = float(self.ing_table.item(row, 1).text())
            ingredients.append({'name': ing_name, 'quantity': quantity})

        self._model.products().add(name, float(self.price_input.value()), ingredients)

        return super().accept()

class ProductsTab(QWidget):
    def __init__(self, model):
        super().__init__()

        self._model = model

        add_layout = QGridLayout()

        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_product)
        self.del_button = QPushButton("Удалить")
        self.del_button.clicked.connect(self.delete_product)
        self.edit_button = QPushButton("Редактировать")
        self.edit_button.clicked.connect(self.edit_product)

        self.products_table = QTableWidget()
        self.products_table.setColumnCount(2)
        self.products_table.setHorizontalHeaderLabels(["Назавание", "Цена"])
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)  # выделение строк
        self.products_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.products_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.products_table.itemSelectionChanged.connect(self.on_selection_changed)

        add_layout.addWidget(self.add_button, 1, 0)  
        add_layout.addWidget(self.edit_button, 1, 1) 
        add_layout.addWidget(self.del_button, 1, 2) 
        add_layout.addWidget(self.products_table, 2, 0, 1, 3)  
    
        self.setLayout(add_layout)

        self.update_products_table()

    def on_selection_changed(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            product_name = self.products_table.item(selected_row, 0).text()
            # Здесь можно добавить логику для обработки выбранного продукта
            print(f"Выбран продукт: {product_name}")    

    def add_product(self):
        dialog = CreateProductDialog(self._model)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.update_products_table()

    def edit_product(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите продукт для редактирования.")
            return

        selected_row = selected_rows[0].row()
        product_name = self.products_table.item(selected_row, 0).text()
        product = None
        for prod in self._model.products().data():
            if prod.name == product_name:
                product = prod
                break

        if not product:
            QMessageBox.warning(self, "Ошибка", "Продукт не найден.")
            return

        dialog = CreateProductDialog(self._model)
        dialog.name_input.setText(product.name)
        dialog.price_input.setValue(product.price)
        for ing in product.ingredients:
            row_position = dialog.ing_table.rowCount()
            dialog.ing_table.insertRow(row_position)
            dialog.ing_table.setItem(row_position, 0, QTableWidgetItem(ing['name'])) 
            dialog.ing_table.setItem(row_position, 1, QTableWidgetItem(str(ing['quantity'])))
            ing_obj = self._model.ingredients().by_name(ing['name'])
            dialog.ing_table.setItem(row_position, 2, QTableWidgetItem(entities.UNIT_NAMES[ing_obj.unit]))

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return          

        # Удаляем старый продукт и добавляем новый с обновленными данными
        self._model.products().delete(product.name)
        ingredients = []
        for row in range(dialog.ing_table.rowCount()):
            ing_name = dialog.ing_table.item(row, 0).text()
            quantity = float(dialog.ing_table.item(row, 1).text())
            ingredients.append({'name': ing_name, 'quantity': quantity})

        self._model.products().add(dialog.name_input.text().strip(), float(dialog.price_input.value()), ingredients)

        self.update_products_table()    

    def delete_product(self):
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Ошибка", "Выберите продукт для удаления.")
            return

        selected_row = selected_rows[0].row()
        product_name = self.products_table.item(selected_row, 0).text()

        confirm = QMessageBox.question(
            self, "Подтверждение удаления",
            f"Вы уверены, что хотите удалить продукт '{product_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            self._model.products().delete(product_name)
            self.update_products_table()

    def update_products_table(self):
        data = self._model.products().data()
        self.products_table.clearContents()
        self.products_table.setRowCount(len(data))

        for i, row in enumerate(data):
            self.products_table.setItem(i, 0, QTableWidgetItem(row.name))
            self.products_table.setItem(i, 1, QTableWidgetItem(str(row.price)))  

class ProductsWidget(QWidget):
    
    def __init__(self, model):
        super().__init__()
        
        main_layout = QVBoxLayout()
        
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(ProductsTab(model), "Продукция")
        self.tab_widget.addTab(IngredientsTab(model), "Ингредиенты")

        main_layout.addWidget(self.tab_widget)
        
        self.setLayout(main_layout)
