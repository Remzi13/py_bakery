from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QLineEdit, QComboBox, QLabel, QMessageBox, QSpinBox
)

class CreateExpenseTypeDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Тип расходов")
        self._model = model
        layout =  QGridLayout()

        self.name_input = QLineEdit()
        self.category_combo = QComboBox()        
        self.category_combo.addItems(self._model.utils().get_expense_category_names())
        self.category_combo.currentIndexChanged.connect(self.update_table)

        self.price = QSpinBox()        
        self.price.setRange(0, 1000000)        
        self.price.setSingleStep(1)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Назавание", "Цена", "Категория"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.add_type)

        del_button = QPushButton("Удалить")
        del_button.clicked.connect(self.del_type)
        
        layout.addWidget(QLabel("Название:"), 0, 0)
        layout.addWidget(self.name_input, 0, 1)
        layout.addWidget(QLabel("Тип:"), 1, 0)
        layout.addWidget(self.category_combo, 1, 1)
        layout.addWidget(QLabel("Цена:"), 2, 0)
        layout.addWidget(self.price, 2, 1)
        layout.addWidget(self.table, 3, 0, 1, 2)
        layout.addWidget(add_button, 4, 0)
        layout.addWidget(del_button, 4, 1)

        self.setLayout(layout)

        self.update_table()

    def update_table(self):
        selected_category_name = self.category_combo.currentText()
    
        # 1. Загрузка отфильтрованных данных: Фильтрация выполняется в БД
        expense_types = self._model.expense_types().get_by_category_name(selected_category_name)
    
        self.table.clearContents()
        self.table.setRowCount(len(expense_types))
    
        # 2. Оптимизация: Так как все строки имеют ОДНУ и ту же категорию, 
        # мы можем получить ее имя один раз, используя UtilsRepository.
        # Если список пуст, name_for_display будет None.
        name_for_display = self._model.utils().get_expense_category_name_by_id(
            expense_types[0].category_id
        ) if expense_types else ""

        for i, row in enumerate(expense_types):
            # 3. Заполнение таблицы
            self.table.setItem(i, 0, QTableWidgetItem(row.name))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.default_price))) 
        
            # 4. Использование заранее полученного имени категории
            self.table.setItem(i, 2, QTableWidgetItem(name_for_display))

    def add_type(self):
        name = self.name_input.text()
        category = self.category_combo.currentText()
        price = self.price.value()   

        if name == "":
            QMessageBox.warning(self, "Ошибка", "Имя не может быть пустым.")
            return 

        self._model.expense_types().add(name, price, category)

        self.update_table()
        
    def del_type(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            name = self.table.item(selected_row, 0).text()
        
            # 1. Получаем строковое имя категории, которое отображается в таблице
            category_name = self.table.item(selected_row, 2).text()
        
            # 2. Проверяем категорию напрямую по имени
            # Мы знаем, что категория для ингредиентов называется 'Сырьё'
            INGREDIENT_CATEGORY_NAME = 'Сырьё' 
        
            if category_name == INGREDIENT_CATEGORY_NAME:
                QMessageBox.warning(self, "Ошибка", "Нелья удалять типы расходов, связанные с ингредиентами ('Сырьё').")
                return
            
            # 3. Удаляем тип расхода по имени
            self._model.expense_types().delete(name)

            self.update_table()

class AddExpenseDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Добавить")
        self._model = model
        layout =  QGridLayout()

        expense_types = self._model.expense_types().data()
        
        self.name_combo = QComboBox()
        names = []
        for i in expense_types:
            names.append(i.name)
        self.name_combo.addItems(names)
        self.name_combo.currentIndexChanged.connect(self.name_changed)

        self.category_combo = QComboBox()
        self.category_combo.addItem("Все")
        names = self._model.utils().get_expense_category_names()
        self.category_combo.addItems(names)
        self.category_combo.currentIndexChanged.connect(self.category_changed)

        self.price = QSpinBox()            
        self.price.setRange(1, 1000000)        
        self.price.setSingleStep(1)
        self.price.setValue(expense_types[0].default_price)
        
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 1000)
        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.accept)

        layout.addWidget(QLabel("Категория:"), 0, 0)
        layout.addWidget(self.category_combo, 0, 1)               
        layout.addWidget(QLabel("Название:"), 1, 0)
        layout.addWidget(self.name_combo, 1, 1)
        layout.addWidget(QLabel("Цена:"), 2, 0)
        layout.addWidget(self.price, 2, 1)
        layout.addWidget(QLabel("Количество:"), 3, 0)
        layout.addWidget(self.quantity, 3, 1)
        layout.addWidget(save_button, 4, 0, 1, 2)

        self.setLayout(layout)
    
    def name_changed(self):
        name = self.name_combo.currentText()
        if name is not None:
            self.price.setValue(self._model.expense_types().get(name).default_price)

    def category_changed(self):
        selected_category = self.category_combo.currentText()
        self.name_combo.clear()

        if selected_category == "Все":            
            names = [e.name for e in self._model.expense_types().data()]
        else:            
            names = self._model.expense_types().get_names_by_category_name(selected_category)            

        if len(names) > 0:
            self.price.setValue(self._model.expense_types().get(names[0]).default_price)
        self.name_combo.addItems(names)

    def accept(self):
        name = self.name_combo.currentText()
        price = self.price.value()
        quantity = self.quantity.value()

        expense_type = self._model.expense_types().get(name)
    
        # Получаем ID категории "Сырьё" из модели (если нужно сравнение)
        # Это можно сделать один раз при инициализации класса диалога, 
        # но для простоты я делаю это здесь:
        ingredient_category_id = self._model.utils().get_expense_category_id_by_name('Сырьё')
    
        if expense_type.category_id == ingredient_category_id: # <-- СРАВНЕНИЕ ПО ID!
            # Если это покупка сырья, мы добавляем количество на склад
            self._model.stock().update(name, quantity)

        # 2. Фиксация расхода: Метод add() в ExpensesRepository должен быть обновлен,
        # чтобы принимать name, price, quantity и самостоятельно извлекать category_id
        # через expense_type.get(name).
        # *Проверь свой ExpensesRepository, убедись, что он корректно использует category_id*
        self._model.expenses().add(name, price, quantity) 
    
        return super().accept()

class ExpensesWidget(QWidget):

    def __init__(self, model):
        super().__init__()    

        self._model = model

        layout =  QGridLayout()

        create_button = QPushButton("Создать")
        create_button.clicked.connect(self.create_expense_type)
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.add_expense)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Назавание", "Цена", "Количество", "Категория", "Дата"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(add_button, 0, 0)
        layout.addWidget(create_button, 0, 1)
        layout.addWidget(self.table, 1, 0, 1, 2)        

        self.setLayout(layout)

        self.update_table()

    def update_table(self): 
        # Получаем все расходы (предполагаем, что expenses().data() возвращает Expense-объекты)
        expenses = self._model.expenses().data()
    
        self.table.clearContents()
        self.table.setRowCount(len(expenses))

        for i, row in enumerate(expenses): 
        
            # 1. Используем UtilsRepository для преобразования ID в имя.
            # ПРИМЕЧАНИЕ: Мы используем row.category, предполагая, что теперь оно содержит числовой ID.
            category_name = self._model.utils().get_expense_category_name_by_id(row.category_id) 

            self.table.setItem(i, 0, QTableWidgetItem(row.name))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.price))) 
            self.table.setItem(i, 2, QTableWidgetItem(str(row.quantity)))
            self.table.setItem(i, 3, QTableWidgetItem(category_name)) # <-- Используем полученное имя
            self.table.setItem(i, 4, QTableWidgetItem(row.date))

    def create_expense_type(self):
        dialog = CreateExpenseTypeDialog(self._model)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        return
    
    def add_expense(self):
        if self._model.expense_types().empty():
            QMessageBox.warning(self, "Ошибка", "Не создано не одного типа расходов.")
            return
        dialog = AddExpenseDialog(self._model)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        self.update_table()
        return
    
