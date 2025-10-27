from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QTableWidget, QTableWidgetItem
)

class StorageWidget(QWidget):
    
    def __init__(self, model):
        super().__init__()    

        self._model = model
        layout =  QGridLayout()    

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Название", "Тип", "Количество"])

        layout.addWidget(self.table, 0, 0)

        self.setLayout(layout)

        self.update_storage_table()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_storage_table()

    def update_storage_table(self):
        data = self._model.get_stock()
        self.table.clearContents()
        self.table.setRowCount(len(data))

        for i, row in enumerate(data):            
            self.table.setItem(i, 0, QTableWidgetItem(row.name()))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.category())))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.quantity())))


