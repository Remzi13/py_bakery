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
from model.expenses import Expenses

class Model:

    def __init__(self):
        # Добавлены явные типы для ясности
        self._ingredients = Ingredients(self)
        self._products = Products(self)
        self._stock = Stock(self)
        self._sales = Sales(self)
        self._expense_types = ExpenseTypes()
        self._expenses = Expenses(self)
 
    #todo remove use only in ingredients.py
    def add_stock_item(self, name, category, quantity, ing_id):        
        self._stock.add(name=name, category=category, quantity=quantity, inv_id=ing_id)
    
    def delete_stock_item(self, name):
        self._stock.delete(name)        

    def update_stock_item(self, name, quantity):
        self._stock.update(name, quantity)

    def calculate_income(self):        
        return sum(sale.price * sale.quantity for sale in self._sales.data())

    def calculate_expenses(self):        
        return sum(expense.price * expense.quantity for expense in self._expenses.data())

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
 
    def expenses(self):
        return self._expenses
    
    def save_to_xml(self):
        root = ET.Element("bakery")

        self._ingredients.save_to_xml(root)
        self._products.save_to_xml(root)               
        self._stock.save_to_xml(root)                
        self._sales.save_to_xml(root)
        self._expense_types.save_to_xml(root)
        self._expenses.save_to_xml(root)
                
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

        except FileNotFoundError:
            pass  # Файл не найден, начинаем с пустых данных
    
    