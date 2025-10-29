import xml.etree.ElementTree as ET
import uuid
from datetime import datetime
# Импортируем dataclasses для автоматизации работы с классами данных
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union

# --- Структуры данных (Refactored to dataclasses) ---

# Вложенные классы вынесены на верхний уровень для чистоты и удобства
# (frozen=True делает объект неизменяемым после создания)

@dataclass(frozen=True)
class Ingredient:
    """Сырье для производства."""
    name: str
    unit: str
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass(frozen=True)
class Product:
    """Готовый продукт для продажи."""
    name: str
    price: int
    ingredients: List[Dict[str, Any]]  # Список ингредиентов с их количеством
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass
class Inventory:
    """Инвентарь/Запас (изменяемый)."""
    name: str
    category: int
    quantity: float  # float для более точного учета (вместо int)
    inv_id: uuid.UUID

@dataclass(frozen=True)
class Sale:
    """Проданный продукт."""
    product_name: str
    price: int
    quantity: float
    product_id: uuid.UUID
    # Используем field(default_factory) для генерации даты по умолчанию
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

@dataclass(frozen=True)
class ExpenseType:
    """Тип расхода (например, 'Аренда', 'Мука')."""
    name: str
    default_price: int
    category: int
    id: uuid.UUID = field(default_factory=uuid.uuid4)

@dataclass(frozen=True)
class Expense:
    """Фактический расход, зафиксированный во времени."""
    name: str
    price: int
    category: int
    quantity: float
    type_id: uuid.UUID
    date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

class Model:

    UNITS_NAME = ['кг', 'грамм', 'литр', 'штуки']

    class Category:
        INGREDIENT = 0
        ENVIRONMENT = 1  # ИСПРАВЛЕНО: ENVIROMENT -> ENVIRONMENT
        PAYMENT = 2

    # ИСПРАВЛЕНО: 'платижи' -> 'платежи'
    CATEGORY_NAMES = ['ингредиенты', 'оборудование', 'платежи']

    # Переопределяем атрибуты Model, чтобы сохранить совместимость с внешним кодом,
    # который может обращаться к Model.Ingredient и т.д.
    Ingredient = Ingredient
    Product = Product
    Inventory = Inventory
    Sale = Sale
    ExpenseType = ExpenseType
    Expense = Expense

    def __init__(self):
        # Добавлены явные типы для ясности
        self._ingredients: List[self.Ingredient] = []
        self._products: List[self.Product] = []
        self._stock: List[self.Inventory] = []
        self._sales: List[self.Sale] = []
        self._expense_types: List[self.ExpenseType] = []
        self._expenses: List[self.Expense] = []
        

    # --- Методы-геттеры (используют прямой доступ к атрибутам dataclasses) ---

    def get_units(self):
        return self.UNITS_NAME

    def get_ingredient(self, name: str) -> Optional[Ingredient]:
        """Ищет ингредиент по имени."""
        return next((i for i in self._ingredients if i.name == name), None)

    def get_ingredients_names(self):
        return [i.name for i in self._ingredients]

    def get_ingredient_by_id(self, id: uuid.UUID) -> Optional[Ingredient]:
        return next((i for i in self._ingredients if i.id == id), None)

    def get_product_by_name(self, name: str) -> Optional[Product]:
        return next((p for p in self._products if p.name == name), None)

    def get_products_names(self):
        return [p.name for p in self._products]

    def get_expense_type(self, name: str) -> Optional[ExpenseType]:
        return next((et for et in self._expense_types if et.name == name), None)
    

    def add_ingredient(self, name, unit):
        self._ingredients.append(self.Ingredient(name=name, unit=unit))
        # add_inventory и add_expense_type теперь используют get_ingredient для ID
        self.add_inventory(name, self.Category.INGREDIENT, 0)
        self.add_expense_type(name, 100, self.Category.INGREDIENT)

    def delete_ingredient(self, name):
        ingredient = self.get_ingredient(name)
        products = self.get_products()
        for product in products:           
            for ing in product.ingredients:
                if ing['name'] == name:
                    raise ValueError(f"Ингредиент '{name}' используется в продукте '{product.name}'. Удаление невозможно.")
        if ingredient:
            self._ingredients = [ing for ing in self._ingredients if ing.name != name]
            # Удаляем связанные записи в инвентаре и типах расходов
            self._stock = [item for item in self._stock if item.inv_id != ingredient.id]
            self._expense_types = [et for et in self._expense_types if et.name != name]

    def add_product(self, name, price, ingredients: List[Dict]):
        new_product = self.Product(name=name, price=price, ingredients=ingredients)

        # Логика обновления продукта, если он уже существует
        for i, product in enumerate(self._products):
            if product.name == name:
                self._products[i] = new_product
                return

        self._products.append(new_product)

    def delete_product(self, name):
        self._products = [product for product in self._products if product.name != name]

    def add_inventory(self, name, category, quantity):
        ing = self.get_ingredient(name)
        if not ing:             
             raise ValueError(f"Ингредиент '{name}' не найден. Невозможно добавить в инвентарь.")

        self._stock.append(self.Inventory(name=name, category=category, quantity=quantity, inv_id=ing.id))

    def update_inventory(self, name, quantity):
        for item in self._stock:
            if item.name == name:
                # Inventory - dataclass, но не frozen, можно менять напрямую
                item.quantity += quantity
                return        
        raise KeyError(f"Элемент '{name}' не найден в инвентаре")

    def add_sale(self, name, price, quantity):
        product = self.get_product_by_name(name)

        if product:
            for i in product.ingredients:
                # Используем прямой доступ к ключам словаря i['name'], i['quantity']
                # (В идеале ingredients должны быть dataclass'ами, но для совместимости оставим так)
                self.update_inventory(i['name'], -i['quantity'] * quantity)

            self._sales.append(self.Sale(product_name=name, price=price, quantity=quantity, product_id=product.id))
        else:
            # УЛУЧШЕНИЕ: Замена assert False на ValueError
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
        # Используем прямой доступ к атрибутам
        return sum(sale.price * sale.quantity for sale in self._sales)

    def calculate_expenses(self):
        # ИСПРАВЛЕНА КРИТИЧЕСКАЯ ОШИБКА: теперь суммируется price * quantity
        return sum(expense.price * expense.quantity for expense in self._expenses)

    def calculate_profit(self):
        return self.calculate_income() - self.calculate_expenses()

    # --- Методы, возвращающие списки ---
    # Оставлены без изменений

    def get_ingredients(self):
        return self._ingredients

    def get_products(self):
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

        ingredients_elem = ET.SubElement(root, "ingredients")
        for ingredient in self._ingredients:
            ing_elem = ET.SubElement(ingredients_elem, "ingredient")
            ET.SubElement(ing_elem, "name").text = ingredient.name
            ET.SubElement(ing_elem, "unit").text = str(ingredient.unit)
            ET.SubElement(ing_elem, "id").text = str(ingredient.id)

        products_elem = ET.SubElement(root, "products")
        for product in self._products:
            prod_elem = ET.SubElement(products_elem, "product")
            ET.SubElement(prod_elem, "id").text = str(product.id)
            ET.SubElement(prod_elem, "name").text = product.name
            ET.SubElement(prod_elem, "price").text = str(product.price)
            ingredients_list_elem = ET.SubElement(prod_elem, "ingredients")
            for ing in product.ingredients:
                ing_elem = ET.SubElement(ingredients_list_elem, "ingredient")
                ET.SubElement(ing_elem, "ing_id").text = str(self.get_ingredient(ing['name']).id) 
                ET.SubElement(ing_elem, "name").text = ing['name']
                ET.SubElement(ing_elem, "quantity").text = str(ing['quantity'])
                
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

            self._ingredients.clear()
            if root.find("products") is not None:
                for ing_elem in root.find("ingredients").findall("ingredient"):
                    name = ing_elem.find("name").text
                    unit = int(ing_elem.find("unit").text)
                    id = ing_elem.find("id").text
                    self._ingredients.append(Model.Ingredient(name, unit, uuid.UUID(id))) 

            self._products.clear()
            if root.find("products") is not None:
                for prod_elem in root.find("products").findall("product"):
                    name = prod_elem.find("name").text
                    price = float(prod_elem.find("price").text)
                    id = prod_elem.find("id").text
                    ingredients = []
                    for ing_elem in prod_elem.find("ingredients").findall("ingredient"):
                        ing_name = ing_elem.find("name").text
                        quantity = float(ing_elem.find("quantity").text)
                        ing_id = ing_elem.find("ing_id").text
                        ingredients.append({'name': ing_name, 'quantity': quantity})                
                    self._products.append(Model.Product(name, price, ingredients, uuid.UUID(id)))
            
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
    
    