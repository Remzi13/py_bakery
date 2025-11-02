from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QDialog, QMessageBox, QDoubleSpinBox, QLabel
)

import model.entities as entities

class EditStockDialog(QDialog):

    def __init__(self, model, name):
        super().__init__()
        self.setWindowTitle("Редактировать")
        self._model = model
        self._name = name
        item = self._model.stock().get(name)
        
        self.quantity = QDoubleSpinBox()
        self.quantity.setRange(-1000.0, 1000.0)
        self.quantity.setValue(item.quantity)

        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save)

        layout =  QGridLayout()
        layout.addWidget(QLabel(f"Название: {name}"), 0, 0)
        layout.addWidget(self.quantity, 1, 0)
        layout.addWidget(self.save_button, 2, 0)

        self.setLayout(layout)
    
    def save(self):
        new_quantity = self.quantity.value()
        self._model.stock().set(self._name, new_quantity)
        return super().accept()

class StorageWidget(QWidget):
    
    def __init__(self, model):
        super().__init__()    

        self._model = model
        layout =  QGridLayout()    

        self.edit = QPushButton("Редактировать")
        self.edit.clicked.connect(self.edit_stock)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Название", "Категория", "Количество", "Ед. изм."])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.edit, 0, 0)
        layout.addWidget(self.table, 1, 0)

        self.setLayout(layout)

        self.update_storage_table()

    def edit_stock(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            name = self.table.item(selected_row, 0).text()
            dialog = EditStockDialog(self._model, name)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.update_storage_table()
                return        
        else:
            QMessageBox.warning(self, "Ошибка", "Для редактирования выберите ")

    def showEvent(self, event):
        super().showEvent(event)
        self.update_storage_table()

    def update_storage_table(self):
        data = self._model.stock().data()
        self.table.clearContents()
        self.table.setRowCount(len(data))

        for i, row in enumerate(data):            
            self.table.setItem(i, 0, QTableWidgetItem(row.name))
            self.table.setItem(i, 1, QTableWidgetItem(entities.STOCK_CATEGORY_NAMES[row.category]))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.quantity)))            
            self.table.setItem(i, 3, QTableWidgetItem(entities.UNIT_NAMES[row.unit]))


