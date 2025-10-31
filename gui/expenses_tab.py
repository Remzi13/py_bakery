from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QLineEdit, QComboBox, QLabel, QDoubleSpinBox
)

import model.entities as entities

class CreateExpenseTypeDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Тип расходов")
        self._model = model
        layout =  QGridLayout()

        self.name_input = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(entities.CATEGORY_NAMES.values())

        self.price = QDoubleSpinBox()        
        self.price.setRange(0.0, 1000.0)
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
        layout.addWidget(self.type_combo, 1, 1)
        layout.addWidget(QLabel("Цена:"), 2, 0)
        layout.addWidget(self.price, 2, 1)
        layout.addWidget(self.table, 3, 0, 1, 2)
        layout.addWidget(add_button, 4, 0)
        layout.addWidget(del_button, 4, 1)

        self.setLayout(layout)

        self.update_table()

    def update_table(self):
        expense_types = self._model.get_expense_types()     
        self.table.clearContents()
        self.table.setRowCount(len(expense_types))

        for i, row in enumerate(expense_types):            
            self.table.setItem(i, 0, QTableWidgetItem(row.name))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.default_price)))              
            self.table.setItem(i, 2, QTableWidgetItem(entities.CATEGORY_NAMES[int(row.category)]))

    def add_type(self):
        name = self.name_input.text()
        category = self.type_combo.currentIndex()
        price = self.price.value()        
        self._model.add_expense_type(name, price, category)

        self.update_table()
        
    def del_type(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            name = self.table.item(selected_row, 0).text()
            self._model.delete_expense_type(name)

            self.update_table()

class AddExpenseDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Добавить")
        self._model = model
        layout =  QGridLayout()

        expense_types = self._model.get_expense_types()
        self.type_label = QLabel("Тип: {}".format(entities.CATEGORY_NAMES[expense_types[0].category]))

        self.type_combo = QComboBox()
        self.type_combo.currentIndexChanged.connect(self.type_changed)
        
        names = []
        for i in expense_types:
            names.append(i.name)
        self.type_combo.addItems(names)

        self.price = QDoubleSpinBox()            
        self.price.setRange(0.0, 1000.0)
        self.price.setDecimals(2)
        self.price.setSingleStep(0.1)
        self.price.setValue(expense_types[0].default_price)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(self.accept)

        layout.addWidget(QLabel("Название:"), 0, 0)
        layout.addWidget(self.type_combo, 0, 1)
        layout.addWidget(self.type_label, 1, 0)        
        layout.addWidget(QLabel("Цена:"), 2, 0)
        layout.addWidget(self.price, 2, 1)
        layout.addWidget(save_button, 3, 0, 1, 2)

        self.setLayout(layout)
    
    def type_changed(self):
        index = self.type_combo.currentIndex()
        expense_types = self._model.get_expense_types()
        self.type_label.setText("Тип: {}".format(entities.CATEGORY_NAMES[expense_types[index].category]))

    def accept(self):
        name = self.type_combo.currentText()
        price = self.price.value()
        self._model.add_expense(name, price, 1)
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
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Назавание", "Цена", "Категория", "Дата"])
        #self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(add_button, 0, 0)
        layout.addWidget(create_button, 0, 1)
        layout.addWidget(self.table, 1, 0, 1, 2)        

        self.setLayout(layout)

        self.update_table()

    def update_table(self):           
        expenses = self._model.get_expenses()
        self.table.clearContents()
        self.table.setRowCount(len(expenses))

        for i, row in enumerate(expenses):            
            self.table.setItem(i, 0, QTableWidgetItem(row.name))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.price)))              
            self.table.setItem(i, 2, QTableWidgetItem(entities.CATEGORY_NAMES[int(row.category)]))
            self.table.setItem(i, 3, QTableWidgetItem(row.date))


    def create_expense_type(self):
        dialog = CreateExpenseTypeDialog(self._model)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        return
    
    def add_expense(self):
        dialog = AddExpenseDialog(self._model)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        self.update_table()
        return
    
