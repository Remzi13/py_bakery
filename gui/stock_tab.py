from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QTableWidgetItem, QPushButton, QDialog, QMessageBox, QDoubleSpinBox, QLabel
)

import gui.widgets as widgets

class EditStockDialog(QDialog):

    def __init__(self, model, name : str, writeoff : bool):
        super().__init__()
        
        self._model = model
        self._name = name
        self._writeoff = writeoff

        if writeoff:
            self.setWindowTitle("Списание")
        else:
            self.setWindowTitle("Редактировать")
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
        if self._writeoff:
            self._model.writeoffs().add(self._name, "stock", new_quantity,"спсание")
        else:
            new_quantity = self.quantity.value()
            self._model.stock().set(self._name, new_quantity)
        return super().accept()

class StorageWidget(QWidget):
    
    def __init__(self, model):
        super().__init__()    

        self._model = model
        layout =  QGridLayout()    

        edit_button = QPushButton("Редактировать")
        edit_button.clicked.connect(lambda: self.edit_stock(False))

        writeoff_button = QPushButton("Списание")        
        writeoff_button.clicked.connect(lambda: self.edit_stock(True))

        self.table = widgets.TableWidget("Склад", ["Название", "Категория", "Количество", "Ед. изм."] )
        
        layout.addWidget(edit_button, 0, 0)
        layout.addWidget(writeoff_button, 0, 1)
        layout.addWidget(self.table, 1, 0, 1, 2)

        self.setLayout(layout)

        self.update_storage_table()

    def edit_stock(self, writeoff):
        selected_rows = self.table.selectedRows()
        if selected_rows:
            selected_row = selected_rows[0].row()
            name = self.table.item(selected_row, 0).text()
            dialog = EditStockDialog(self._model, name, writeoff)
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
        self.table.clear(len(data))

        for i, row in enumerate(data):            
            self.table.setItem(i, 0, QTableWidgetItem(row.name))
            category_name = self._model.utils().get_stock_category_name_by_id(row.category_id)
            self.table.setItem(i, 1, QTableWidgetItem(category_name))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.quantity)))
            unit_name = self._model.utils().get_unit_name_by_id(row.unit_id)
            self.table.setItem(i, 3, QTableWidgetItem(unit_name))


