from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QPushButton, QDialog, QTableWidget, 
    QComboBox, QSpinBox, QLabel, QTableWidgetItem, QHeaderView, QDoubleSpinBox, QGroupBox, QVBoxLayout, QTextEdit
)

import gui.widgets as widgets

class SaleDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Продажа")
        self.setGeometry(150, 150, 300, 200)
        self._model = model
        layout = QGridLayout()

        self.product_combo = QComboBox()        
        self.product_combo.addItems(self._model.products().names())
        self.product_combo.currentIndexChanged.connect(self.product_changed)

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.accept)    

        self.price = QSpinBox()        
        self.price.setRange(0, 10000)
        self.price.setSingleStep(1)
        self.product_changed()

        self.quantity = QSpinBox()
        self.quantity.setRange(1, 1000)

        self.discount = QSpinBox()
        self.discount.setRange(0, 100)

        layout.addWidget(QLabel("Навание"), 0, 0)
        layout.addWidget(self.product_combo, 0, 1)
        layout.addWidget(QLabel("Цена"), 1, 0)
        layout.addWidget(self.price, 1, 1)
        layout.addWidget(QLabel("Количество"), 2, 0)
        layout.addWidget(self.quantity, 2, 1)
        layout.addWidget(QLabel("Скидка"), 3, 0)
        layout.addWidget(self.discount, 3, 1)
        layout.addWidget(add_button, 4, 0, 1, 2)

        self.setLayout(layout)
    
    def product_changed(self):
        product_name = self.product_combo.currentText()
        product = self._model.products().by_name(product_name)
        if product:
            self.price.setValue(product.price)
    
    def accept(self):
        name = self.product_combo.currentText()
        price = self.price.value()
        quantity = self.quantity.value()
        discount = self.discount.value()
        self._model.sales().add(name, price, quantity, discount)

        return super().accept()

class WriteoffDialog(QDialog):
    def __init__(self, model):
        super().__init__()
        self.setWindowTitle("Cписание")
        self._model = model

        self.product_combo = QComboBox()
        self.product_combo.addItems(model.products().names())        

        self.quantity = QDoubleSpinBox()
        self.quantity.setRange(1, 100)

        save_button = QPushButton("Списать")
        save_button.clicked.connect(self.save)

        layout = QGridLayout()

        text_group = QGroupBox("Причина")
        text_layout = QVBoxLayout()
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Введите текст здесь...")
        text_layout.addWidget(self.text_edit)
        text_group.setLayout(text_layout)

        
        layout.addWidget( QLabel("Продукт:"), 0, 0)
        layout.addWidget(self.product_combo, 0, 1)
        layout.addWidget(QLabel("Количество:"), 1, 0)
        layout.addWidget(self.quantity, 1, 1)
        layout.addWidget(text_group, 2, 0, 1, 2)

        layout.addWidget(save_button, 3, 0, 1, 2)

        self.setLayout(layout)

    def save(self):
        prod_name = self.product_combo.currentText()
        quantity = self.quantity.value()
        reason = self.text_edit.toPlainText()
        self._model.writeoffs().add(prod_name, "product", quantity, reason)
        return super().accept()


class MainWidget(QWidget):
    
    def __init__(self, model):
        super().__init__()        

        self.model = model

        layout =  QGridLayout()

        self.income = QLabel("Доход: {:.2f}.".format(self.model.calculate_income()))
        self.expenses = QLabel("Расходы: {:.2f}.".format(self.model.calculate_expenses()))
        self.profit = QLabel("Прибыль: {:.2f}.".format(self.model.calculate_profit()))   

        sale_button = QPushButton("Продажа")
        sale_button.clicked.connect(self.add_sale)

        writeoff_button = QPushButton("Списание")
        writeoff_button.clicked.connect(self.writeoff)

        self.sales_table = widgets.TableWidget("Продажи", ["Названи", "Количество", "Цена", "Скидка", "Дата"])        
        self.writeoff_table = widgets.TableWidget("Списания", ["Названи", "Количество", "Дата"])
        
        layout.addWidget(self.income, 0, 0)
        layout.addWidget(self.expenses, 0, 1)
        layout.addWidget(self.profit, 0, 2)        
        layout.addWidget(sale_button, 1, 0, 1, 2 )
        layout.addWidget(writeoff_button, 1, 2, 1, 1)
        layout.addWidget(self.sales_table, 2, 0, 1, 3)        
        layout.addWidget(self.writeoff_table, 3, 0, 1, 3)

        self.setLayout(layout)

        self.update_sales_table()
        self.update_writeoff_table()

        
    def update_sales_table(self):
        data = self.model.sales().data()
        self.sales_table.clear(len(data))
        
        for i, row in enumerate(data):            
            self.sales_table.setItem(i, 0, QTableWidgetItem(row.product_name))
            self.sales_table.setItem(i, 1, QTableWidgetItem(str(row.quantity)))
            self.sales_table.setItem(i, 2, QTableWidgetItem(str(round(row.price, 3))))
            self.sales_table.setItem(i, 3, QTableWidgetItem(str(row.discount)))
            self.sales_table.setItem(i, 4, QTableWidgetItem(row.date))

        self.income.setText("Доход: {:.2f}.".format(self.model.calculate_income()))
        self.expenses.setText("Расходы: {:.2f}.".format(self.model.calculate_expenses()))
        self.profit.setText("Прибыль: {:.2f}.".format(self.model.calculate_profit()))   

    
    def update_writeoff_table(self):
        data = self.model.writeoffs().data()
        self.writeoff_table.clear(len(data))        

        for i, row in enumerate(data):     
            product_name = self.model.products().by_id(row.product_id).name
            self.writeoff_table.setItem(i, 0, QTableWidgetItem(product_name))
            self.writeoff_table.setItem(i, 1, QTableWidgetItem(str(row.quantity)))            
            self.writeoff_table.setItem(i, 2, QTableWidgetItem(row.date))
    
    def add_sale(self):
        dialog = SaleDialog(self.model)        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return        
        self.update_sales_table()

    def writeoff(self):
        dialog = WriteoffDialog(self.model)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.update_writeoff_table()
        