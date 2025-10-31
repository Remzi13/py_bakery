import xml.etree.ElementTree as ET
import uuid
from datetime import datetime

from typing import List, Dict, Any, Optional, Union

from model.entities import Sale, ExpenseType, Expense

from model.ingredients import Ingredients
from model.products import Products
from model.stock import Stock
from model.sales import Sales
from model.expenses import ExpenseTypes

class Model:

    # Переопределяем атрибуты Model, чтобы сохранить совместимость с внешним кодом,
    # который может обращаться к Model.Ingredient и т.д.                
    Expense = Expense

    def __init__(self):
        # Добавлены явные типы для ясности
        self._ingredients = Ingredients(self)
        self._products = Products(self)
        self._stock = Stock(self)
        self._sales = Sales(self)
        self._expense_types = ExpenseTypes(self)
        self._expenses: List[self.Expense] = []
 
    #todo remove use only in ingredients.py
    def add_stock_item(self, name, category, quantity, ing_id):        
        self._stock.add(name=name, category=category, quantity=quantity, inv_id=ing_id)
    
    def delete_stock_item(self, name):
        self._stock.delete(name)        

    def update_stock_item(self, name, quantity):
        self._stock.update(name, quantity)


    def add_expense(self, name, price, quantity):
        expense_type = self.expense_types().get(name)
        if not expense_type:
             raise ValueError(f"Тип расхода '{name}' не найден.")

        self._expenses.append(self.Expense(name=name, price=price, category=expense_type.category,
                                            quantity=quantity, type_id=expense_type.id))

    def calculate_income(self):        
        return sum(sale.price * sale.quantity for sale in self._sales.data())

    def calculate_expenses(self):        
        return sum(expense.price * expense.quantity for expense in self._expenses)

    def calculate_profit(self):
        return self.calculate_income() - self.calculate_expenses()

    # --- Методы, возвращающие списки ---    

    def ingredients(self):
        return self._ingredients

    def products(self):
        return self._products
    
    def stock(self):
        return self._stock

    def sales(self):
        return self._sales

    def expense_types(self):
        return self._expense_types
 
    def get_expenses(self):
        return self._expenses
    
    def save_to_xml(self):
        root = ET.Element("bakery")

        self._ingredients.save_to_xml(root)
        self._products.save_to_xml(root)               
        self._stock.save_to_xml(root)                
        self._sales.save_to_xml(root)
        self._expense_types.save_to_xml(root)
        
        expenses = ET.SubElement(root, "expenses")
        for expense in self._expenses:
            expense_elem = ET.SubElement(expenses, "expense")
            ET.SubElement(expense_elem, "type_id").text = str(expense.type_id)
            ET.SubElement(expense_elem, "name").text = expense.name
            ET.SubElement(expense_elem, "price").text = str(expense.price)
            ET.SubElement(expense_elem, "category").text = str(expense.category)
            ET.SubElement(expense_elem, "date").text = str(expense.date)
            ET.SubElement(expense_elem, "quantity").text = str(expense.quantity)

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)  # добавляет отступы
        tree.write("bakery_data.xml", encoding="utf-8", xml_declaration=True)

    def load_from_xml(self):
        try:
            tree = ET.parse("bakery_data.xml")
            root = tree.getroot()

            self._ingredients.load_from_xml(root)
            self._products.load_from_xml(root)
            self._stock.load_from_xml(root)
            self._sales.load_from_xml(root)
            self._expense_types.load_from_xml(root)
            
            self._expenses.clear()
            if root.find("expenses") is not None:
                for expense_elem in root.find("expenses").findall("expense"):
                    name = expense_elem.find("name").text
                    price = float(expense_elem.find("price").text)
                    category = int(expense_elem.find("category").text)
                    type_id = expense_elem.find("type_id").text
                    date = expense_elem.find("date").text
                    quantity = int(expense_elem.find("quantity").text)
                    self._expenses.append(Model.Expense(name, price, category, quantity, uuid.UUID(type_id), date))

        except FileNotFoundError:
            pass  # Файл не найден, начинаем с пустых данных
    
    