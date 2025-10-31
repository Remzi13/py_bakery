import xml.etree.ElementTree as ET
import uuid
from datetime import datetime

from typing import List, Dict, Any, Optional, Union

from model.entities import Inventory, Sale, ExpenseType, Expense

from model.ingredients import Ingredients
from model.products import Products

class Model:

    # Переопределяем атрибуты Model, чтобы сохранить совместимость с внешним кодом,
    # который может обращаться к Model.Ingredient и т.д.    
    Inventory = Inventory
    Sale = Sale
    ExpenseType = ExpenseType
    Expense = Expense

    def __init__(self):
        # Добавлены явные типы для ясности
        self._ingredients = Ingredients(self)
        self._products = Products(self)
        self._stock: List[self.Inventory] = []
        self._sales: List[self.Sale] = []
        self._expense_types: List[self.ExpenseType] = []
        self._expenses: List[self.Expense] = []
        
    # --- Методы-геттеры (используют прямой доступ к атрибутам dataclasses) ---
    def get_products_names(self):
        return [p.name for p in self._products]

    def get_expense_type(self, name: str) -> Optional[ExpenseType]:
        return next((et for et in self._expense_types if et.name == name), None)
    
    #todo remove use only in ingredients.py
    def add_inventory(self, name, category, quantity, ing_id):        
        self._stock.append(self.Inventory(name=name, category=category, quantity=quantity, inv_id=ing_id))
    
    def delete_inventory(self, name):
        self._stock = [inv for inv in self._stock if inv.name != name]

    def update_inventory(self, name, quantity):
        for item in self._stock:
            if item.name == name:
                # Inventory - dataclass, но не frozen, можно менять напрямую
                item.quantity += quantity
                return        
        raise KeyError(f"Элемент '{name}' не найден в инвентаре")

    def add_sale(self, name, price, quantity):
        product = self.products().by_name(name)

        if product:
            for i in product.ingredients:
                # Используем прямой доступ к ключам словаря i['name'], i['quantity']
                # (В идеале ingredients должны быть dataclass'ами, но для совместимости оставим так)
                self.update_inventory(i['name'], -i['quantity'] * quantity)

            self._sales.append(self.Sale(product_name=name, price=price, quantity=quantity, product_id=product.id))
        else:            
            raise ValueError(f"Продукт '{name}' не найден")

    def add_expense_type(self, name, price, category ):
        self._expense_types.append(self.ExpenseType(name=name, default_price=price, category=category))

    def delete_expense_type(self, name):
        self._expense_types = [expense for expense in self._expense_types if expense.name != name]

    def add_expense(self, name, price, quantity):
        expense_type = self.get_expense_type(name)
        if not expense_type:
             raise ValueError(f"Тип расхода '{name}' не найден.")

        self._expenses.append(self.Expense(name=name, price=price, category=expense_type.category,
                                            quantity=quantity, type_id=expense_type.id))

    def calculate_income(self):        
        return sum(sale.price * sale.quantity for sale in self._sales)

    def calculate_expenses(self):        
        return sum(expense.price * expense.quantity for expense in self._expenses)

    def calculate_profit(self):
        return self.calculate_income() - self.calculate_expenses()

    # --- Методы, возвращающие списки ---    

    def ingredients(self):
        return self._ingredients

    def products(self):
        return self._products

    def get_stock(self):
        return self._stock

    def get_sales(self):
        return self._sales

    def get_expense_types(self):
        return self._expense_types

    def get_expense_category_names(self):
        return self.CATEGORY_NAMES

    def get_expenses(self):
        return self._expenses
    
    def save_to_xml(self):
        root = ET.Element("bakery")

        self._ingredients.save_to_xml(root)
        self._products.save_to_xml(root)               
                
        stock_elem = ET.SubElement(root, "stock")
        for item in self._stock:
            item_elem = ET.SubElement(stock_elem, "item")
            ET.SubElement(item_elem, "inv_id").text = str(item.inv_id)
            ET.SubElement(item_elem, "name").text = item.name
            ET.SubElement(item_elem, "category").text = str(item.category)
            ET.SubElement(item_elem, "quantity").text = str(item.quantity)

        sale_elem = ET.SubElement(root, "sales")
        for sale in self._sales:
            sal_elem = ET.SubElement(sale_elem, "sale")
            ET.SubElement(sal_elem, "product_id").text = str(sale.product_id)
            ET.SubElement(sal_elem, "product_name").text = sale.product_name
            ET.SubElement(sal_elem, "price").text = str(sale.price)
            ET.SubElement(sal_elem, "quantity").text = str(sale.quantity)
            ET.SubElement(sal_elem, "date").text = str(sale.date)

        expense_type_elem = ET.SubElement(root, "expense_types")
        for expense_type in self._expense_types:
            expense_elem = ET.SubElement(expense_type_elem, "expense_type")
            ET.SubElement(expense_elem, "id").text = str(expense_type.id)
            ET.SubElement(expense_elem, "name").text = expense_type.name
            ET.SubElement(expense_elem, "default_price").text = str(expense_type.default_price)
            ET.SubElement(expense_elem, "category").text = str(expense_type.category)

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
        ET.indent(tree, space="  ", level=0)  # <-- вот эта строка добавляет отступы
        tree.write("bakery_data.xml", encoding="utf-8", xml_declaration=True)

    def load_from_xml(self):
        try:
            tree = ET.parse("bakery_data.xml")
            root = tree.getroot()

            self._ingredients.load_from_xml(root)
            self._products.load_from_xml(root)
            
            self._stock.clear()
            if root.find("stock") is not None:
                for item_elem in root.find("stock").findall("item"):
                    name = item_elem.find("name").text
                    category = int(item_elem.find("category").text)
                    quantity = float(item_elem.find("quantity").text)
                    inv_id = item_elem.find("inv_id").text                  
                    self._stock.append(Model.Inventory(name, category, quantity, uuid.UUID(inv_id)))    
                
            self._sales.clear()
            if root.find("sales") is not None:  
                for sale_elem in root.find("sales").findall("sale"):
                    product_name = sale_elem.find("product_name").text
                    price = float(sale_elem.find("price").text)
                    quantity = int(sale_elem.find("quantity").text)
                    id = sale_elem.find("product_id").text
                    date = sale_elem.find("date").text
                    self._sales.append(Model.Sale(product_name, price, quantity, uuid.UUID(id), date))

            self._expense_types.clear()
            if root.find("expense_types") is not None:
                for expense_type_elem in root.find("expense_types").findall("expense_type"):
                    name = expense_type_elem.find("name").text
                    default_price = float(expense_type_elem.find("default_price").text)
                    category = int(expense_type_elem.find("category").text)
                    id = expense_type_elem.find("id").text
                    self._expense_types.append(Model.ExpenseType(name, default_price, category, uuid.UUID(id)))            
            
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
    
    