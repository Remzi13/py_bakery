from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QLineEdit, QComboBox, QLabel, QDoubleSpinBox, QMessageBox, QSpinBox
)

import model.entities as entities

class CreateExpenseTypeDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Тип расходов")
        self._model = model
        layout =  QGridLayout()

        self.name_input = QLineEdit()
        self.category_combo = QComboBox()
        self.category_combo.addItems(entities.EXPENSE_CATEGORY_NAMES.values())
        self.category_combo.currentIndexChanged.connect(self.update_table)

        self.price = QDoubleSpinBox()        
        self.price.setRange(0.0, 100000.0)
        self.price.setDecimals(2)
        self.price.setSingleStep(0.1)

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
        expense_types = self._model.expense_types().data()        
        category = entities.category_by_name(self.category_combo.currentText())
        expense_types = [expense for expense in expense_types if expense.category == category]
        self.table.clearContents()
        self.table.setRowCount(len(expense_types))
        for i, row in enumerate(expense_types):
            self.table.setItem(i, 0, QTableWidgetItem(row.name))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.default_price)))              
            self.table.setItem(i, 2, QTableWidgetItem(entities.EXPENSE_CATEGORY_NAMES[int(row.category)]))

    def add_type(self):
        name = self.name_input.text()
        category = self.type_combo.currentIndex()
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
            category = entities.category_by_name(self.table.item(selected_row, 2).text())
            if category == entities.ExpenseCategory.INGREDIENT:
                QMessageBox.warning(self, "Ошибка", "Нелья удалять ингредиенты.")
                return
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
        
        self.category_combo = QComboBox()
        self.category_combo.addItem("Все")
        self.category_combo.addItems(entities.EXPENSE_CATEGORY_NAMES.values())
        self.category_combo.currentIndexChanged.connect(self.category_changed)

        self.price = QDoubleSpinBox()            
        self.price.setRange(0.0, 1000.0)
        self.price.setDecimals(2)
        self.price.setSingleStep(0.1)
        self.price.setValue(expense_types[0].default_price)
        
        self.quantity = QSpinBox()

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
    
    def category_changed(self):
        selected_category = self.category_combo.currentText()
        self.name_combo.clear()

        if selected_category == "Все":            
            names = [e.name for e in self._model.expense_types().data()]
        else:            
            names = [e.name for e in self._model.expense_types().data() if e.category == entities.category_by_name(selected_category)]

        self.name_combo.addItems(names)


    def accept(self):
        
        name = self.name_combo.currentText()
        price = self.price.value()
        quantity = self.quantity.value()

        expense_type = self._model.expense_types().get(name)
        if expense_type.category == entities.ExpenseCategory.INGREDIENT:
            self._model.stock().update(name, quantity)

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
        expenses = self._model.expenses().data()
        self.table.clearContents()
        self.table.setRowCount(len(expenses))

        for i, row in enumerate(expenses):            
            self.table.setItem(i, 0, QTableWidgetItem(row.name))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.price)))              
            self.table.setItem(i, 2, QTableWidgetItem(str(row.quantity)))
            self.table.setItem(i, 3, QTableWidgetItem(entities.EXPENSE_CATEGORY_NAMES[int(row.category)]))
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
    
