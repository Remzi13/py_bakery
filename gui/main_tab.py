from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QDialog, QTableWidget,
    QComboBox, QDoubleSpinBox, QSpinBox, QLabel, QTableWidgetItem
)

class PurchaseDialog(QDialog):

    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Закупка")
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

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.accept)    

        layout.addWidget(QLabel("Навание"), 0, 0)
        layout.addWidget(self.purchase_combo, 0, 1)
        layout.addWidget(QLabel("Цена"), 1, 0)
        layout.addWidget(self.price, 1, 1)
        layout.addWidget(QLabel("Количество"), 2, 0)
        layout.addWidget(self.quantity, 2, 1)
        layout.addWidget(add_button, 3, 0, 1, 2)

        self.setLayout(layout)

    def accept(self):
        name = self.purchase_combo.currentText()
        price = self.price.value()
        quantity = self.quantity.value()
        self.mode.add_expense(name, price, quantity)
        self.mode.update_inventory(name, quantity)

        return super().accept()

class SaleDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Продажа")
        self.setGeometry(150, 150, 300, 200)
        self.mode = model
        layout = QGridLayout()

        self.product_combo = QComboBox()        
        self.product_combo.addItems(model.get_products_names())
        self.product_combo.currentIndexChanged.connect(self.product_changed)

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.accept)    

        self.price = QDoubleSpinBox()        
        self.price.setRange(0.0, 1000.0)
        self.price.setDecimals(2)
        self.price.setSingleStep(0.1)

        self.quantity = QSpinBox()
        self.quantity.setRange(1, 1000)

        layout.addWidget(QLabel("Навание"), 0, 0)
        layout.addWidget(self.product_combo, 0, 1)
        layout.addWidget(QLabel("Цена"), 1, 0)
        layout.addWidget(self.price, 1, 1)
        layout.addWidget(QLabel("Количество"), 2, 0)
        layout.addWidget(self.quantity, 2, 1)
        layout.addWidget(add_button, 3, 0, 1, 2)

        self.setLayout(layout)
    
    def product_changed(self):
        product_name = self.product_combo.currentText()
        product = self.mode.get_product_by_name(product_name)
        if product:
            self.price.setValue(product.price())
    
    def accept(self):
        name = self.product_combo.currentText()
        price = self.price.value()
        quantity = self.quantity.value()
        self.mode.add_sale(name, price, quantity)        

        return super().accept()
    

class MainWidget(QWidget):
    
    def __init__(self, model):
        super().__init__()        

        self.model = model

        layout =  QGridLayout()

        income = QLabel("Доход: {:.2f}.".format(self.model.calculate_income()))
        expenses = QLabel("Расходы: {:.2f}.".format(self.model.calculate_expenses()))
        profit = QLabel("Прибыль: {:.2f}.".format(self.model.calculate_profit()))   

        purchase_button = QPushButton("Закупка")
        purchase_button.clicked.connect(self.add_purchase)

        sale_button = QPushButton("Продажа")
        sale_button.clicked.connect(self.add_sale)
        
        self.purchase_table = QTableWidget()
        self.purchase_table.setColumnCount(4)
        self.purchase_table.setHorizontalHeaderLabels(["Названи", "Количество", "Цена", "Дата"])

        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(4)
        self.sales_table.setHorizontalHeaderLabels(["Названи", "Количество", "Цена", "Дата"])

        layout.addWidget(income, 0, 0)
        layout.addWidget(expenses, 0, 1)
        layout.addWidget(profit, 0, 2)
        layout.addWidget(purchase_button, 1, 0, 1, 3)
        layout.addWidget(self.purchase_table, 2, 0, 1, 3)
        layout.addWidget(sale_button, 3, 0, 1, 3)
        layout.addWidget(self.sales_table, 4, 0, 1, 3)

        self.setLayout(layout)
        
        self.update_purchase_table()
        self.update_sales_table()

    def update_purchase_table(self):
        data = self.model.get_expenses()
        self.purchase_table.clearContents()
        self.purchase_table.setRowCount(len(data))

        for i, row in enumerate(data):            
            self.purchase_table.setItem(i, 0, QTableWidgetItem(row.name()))
            self.purchase_table.setItem(i, 1, QTableWidgetItem(str(row.quantity())))
            self.purchase_table.setItem(i, 2, QTableWidgetItem(str(round(row.price(), 3))))
            self.purchase_table.setItem(i, 3, QTableWidgetItem(row.date()))
    
    def update_sales_table(self):
        data = self.model.get_sales()
        self.sales_table.clearContents()
        self.sales_table.setRowCount(len(data))

        for i, row in enumerate(data):            
            self.sales_table.setItem(i, 0, QTableWidgetItem(row.product_name()))
            self.sales_table.setItem(i, 1, QTableWidgetItem(str(row.quantity())))
            self.sales_table.setItem(i, 2, QTableWidgetItem(str(round(row.price(), 3))))
            self.sales_table.setItem(i, 3, QTableWidgetItem(row.date()))

    def add_purchase(self):
        dialog = PurchaseDialog(self.model)        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return        
        self.update_purchase_table()

    def add_sale(self):
        dialog = SaleDialog(self.model)        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return        
        self.update_sales_table()
        