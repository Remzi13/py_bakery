from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QDialog, QTableWidget,
    QComboBox, QDoubleSpinBox, QSpinBox, QLabel, QTableWidgetItem
)

class PurchaseDialog(QDialog):

    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Добавить закупку")
        self.setGeometry(150, 150, 300, 200)
        self.mode = model
        layout = QGridLayout()
        
        self.purchase_combo = QComboBox()
        # add items to bouth
        self.purchase_combo.addItems(model.get_ingredients_names())

        self.price = QDoubleSpinBox()        
        self.price.setRange(0.0, 1000.0)
        self.price.setDecimals(2)
        self.price.setSingleStep(0.1)

        self.quantity = QSpinBox()
        self.quantity.setRange(1, 1000)

        add = QPushButton("Добавить")
        add.clicked.connect(self.accept)    

        layout.addWidget(QLabel("Навание"), 0, 0)
        layout.addWidget(self.purchase_combo, 0, 1)
        layout.addWidget(QLabel("Цена"), 1, 0)
        layout.addWidget(self.price, 1, 1)
        layout.addWidget(QLabel("Количество"), 2, 0)
        layout.addWidget(self.quantity, 2, 1)
        layout.addWidget(add, 3, 0, 1, 2)

        self.setLayout(layout)

    def accept(self):
        name = self.purchase_combo.currentText()
        price = self.price.value()
        quantity = self.quantity.value()
        self.mode.add_purchase(name, price, quantity)
        self.mode.update_inventory(name, quantity)

        return super().accept()

class MainWidget(QWidget):
    
    def __init__(self, model):
        super().__init__()        

        self.model = model

        layout =  QGridLayout()
        purchase_button = QPushButton("Закупка")
        purchase_button.clicked.connect(self.add_purchase)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Названи", "Количество", "Цена", "Дата"])

        layout.addWidget(purchase_button, 0, 0)
        layout.addWidget(self.table, 1, 0)

        self.setLayout(layout)
        
        self.update_purchase_table()

    def update_purchase_table(self):
        data = self.model.get_purchases()
        self.table.clearContents()
        self.table.setRowCount(len(data))

        for i, row in enumerate(data):            
            self.table.setItem(i, 0, QTableWidgetItem(row.name()))
            self.table.setItem(i, 1, QTableWidgetItem(str(row.quantity())))
            self.table.setItem(i, 2, QTableWidgetItem(str(row.price())))
            self.table.setItem(i, 3, QTableWidgetItem(row.data()))

    def add_purchase(self):

        dialog = PurchaseDialog(self.model)        

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        self.update_purchase_table()
        