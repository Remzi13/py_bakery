import xml.etree.ElementTree as ET

import uuid
from datetime import datetime

class Model:
    
    UNITS_NAME = ['кг', 'грамм', 'литр', 'штуки']

    class Category:
        INGREDIENT = 0
        ENVIROMENT = 1
        PAYMENT = 2

    CATEGORY_NAMES = ['ингридиенты', 'оборудование', 'платижи']

    class Ingredient:
        
        def __init__(self, name: str, unit: str, id: uuid.UUID | None = None):
            self._id = id or uuid.uuid4()
            self._name = name
            self._unit = unit

        def __repr__(self):
            return f"Ingredient(id={self._id}, name='{self._name}', unit='{self._unit}')"

        def name(self):
            return self._name
        
        def unit(self):           
            return self._unit
        
        def id(self):
            return self._id

    class Product:

        def __init__(self, name: str, price: int, ingredients, id: uuid.UUID | None = None):        
            self._id = id or uuid.uuid4()  # если id не передан → генерируем новый
            self._name = name
            self._price = price
            self._ingredients = ingredients  # Список ингредиентов с их количеством

        def __repr__(self):
            return f"Product(id={self._id}, name='{self.name}', price={self.price}, ingredients={self._ingredients})"    
        
        def id(self):
            return self._id

        def name(self):
            return self._name
        
        def price(self):
            return self._price
        
        def ingredients(self):
            return self._ingredients    

    class Inventory:

        def __init__(self, name: str, category, quantity: int, inv_id: uuid.UUID):
            self._inv_id = inv_id
            self._name = name
            self._category = category
            self._quantity = quantity

        def __repr__(self):
            return f"Inventory(id={self._inv_id}, name='{self.name}', category={self.category}, quantity={self.quantity})"

        def inv_id(self):
            return self._inv_id 
        
        def name(self): 
            return self._name
        
        def category(self):
            return self._category
        
        def quantity(self):
            return self._quantity

    class Sale:

        def __init__(self, name: str, price: int, quantity: int, product_id: uuid.UUID, date: str | None = None):
            self._product_id = product_id
            self._product_name = name
            self._date = date or datetime.now().strftime("%Y-%m-%d %H:%M")
            self._price = price
            self._quantity = quantity

        def __repr__(self):
            return f"Sale(product_id={self._product_id}, product_name='{self._product_name}', price={self._price}, quantity={self._quantity})"

        def product_id(self):
            return self._product_id
        
        def product_name(self):
            return self._product_name

        def date(self):
            return self._date
        
        def price(self):
            return self._price
        
        def quantity(self):
            return self._quantity
    
    class ExpenseType():

        def __init__(self, name: str, price: int, category, id: uuid.UUID | None = None):
            self._id = id or uuid.uuid4()
            self._name = name
            self._default_price = price 
            self._category = category

        def id(self):
            return self._id

        def name(self):
            return self._name
        
        def default_price(self):
            return self._default_price
        
        def category(self):
            return self._category

    class Expense():

        def __init__(self, name: str, price: int, category, quantity : int,  type_id: uuid.UUID, date: str | None = None ):
            self._type_id = type_id
            self._name = name
            self._price = price 
            self._category = category
            self._date = date or datetime.now().strftime("%Y-%m-%d %H:%M")
            self._quantity = quantity

        def type_id(self):
            return self._type_id

        def name(self):
            return self._name
        
        def price(self):
            return self._price
        
        def category(self):
            return self._category
        
        def date(self):
            return self._date
        
        def quantity(self):
            return self._quantity

    def __init__(self):
        self._ingredients = []
        self._products = []
        self._stock = []
        self._sales = []
        self._expense_types = []
        self._expenses = []

    def get_units(self):
        return self.UNITS_NAME

    def add_ingredient(self, name, unit):
        self._ingredients.append(Model.Ingredient(name, unit))
        self.add_inventory(name, Model.Category.INGREDIENT, 0)
        self.add_expense_type(name, 100, Model.Category.INGREDIENT)
    
    def get_ingredient(self, name):
        for ingredient in self._ingredients:
            if ingredient.name() == name:
                return ingredient
        return None

    def get_ingredients_names(self):
        return [ingredient.name() for ingredient in self._ingredients]
    
    def get_ingredient_by_id(self, id):
        for ingredient in self._ingredients:
            if ingredient.id() == id:
                return ingredient
        return None 

    def get_ingredients(self):
        return self._ingredients
    
    def add_product(self, name, price, ingredients):
        new_product = Model.Product(name, price, ingredients)
        for prdoduct in self._products:
            if prdoduct.name() == name:
                prdoduct = new_product
                return
        self._products.append(new_product)

    def get_products(self):
        return self._products
    
    def get_product_by_name(self, name):
        for product in self._products:
            if product.name() == name:
                return product
        return None   

    def get_products_names(self):
        return [product.name() for product in self._products]
    
    def delete_product(self, name):
        self._products = [product for product in self._products if product.name() != name]
        
    def add_inventory(self, name, category, quantity):
        ing = self.get_ingredient(name)
        self._stock.append(Model.Inventory(name, category, quantity, ing.id()))

    def update_inventory(self, name, quantity):
        for item in self._stock:
            if item.name() == name:
                item._quantity += quantity
                return
        assert False, "Элемент не найден в инвентаре"

    def get_stock(self):
        return self._stock

    def add_sale(self, name, price, quantity):
        product = None
        for prod in self._products:
            if prod.name() == name:
                product = prod
                break            
        if product:
            for i in product.ingredients():                
                self.update_inventory(i['name'], -i['quantity'] * quantity) 
                
            self._sales.append(Model.Sale(name, price, quantity, product.id()))
        else:
            assert False, "Продукт не найден"
    
    def get_sales(self):
        return self._sales

    def add_expense_type(self, name, price, category ):
        self._expense_types.append(Model.ExpenseType(name, price, category))

    def get_expense_type(self, name):
        for expense_type in self._expense_types:
            if expense_type.name() == name:
                return expense_type
        return None

    def get_expense_types(self):
        return self._expense_types
    

    def delete_expense_type(self, name):
        self._expense_types = [expense for expense in self._expense_types if expense.name() != name]

    def get_expense_category_names(self):
        return Model.CATEGORY_NAMES

    def add_expense(self, name, price, quantity):
        expense_type = self.get_expense_type(name)
        self._expenses.append(Model.Expense(name, price, expense_type.category(), quantity, expense_type.id() ) )

    def get_expenses(self):
        return self._expenses

    def calculate_income(self):
        return sum(sale.price() * sale.quantity() for sale in self._sales)

    def calculate_expenses(self):
        s = sum(expense.price() * expense.quantity() for expense in self._expenses)
        return s
    
    def calculate_profit(self):
        return self.calculate_income() - self.calculate_expenses()

    def save_to_xml(self):
        root = ET.Element("bakery")

        ingredients_elem = ET.SubElement(root, "ingredients")
        for ingredient in self._ingredients:
            ing_elem = ET.SubElement(ingredients_elem, "ingredient")
            ET.SubElement(ing_elem, "name").text = ingredient.name()
            ET.SubElement(ing_elem, "unit").text = str(ingredient.unit())
            ET.SubElement(ing_elem, "id").text = str(ingredient.id())

        products_elem = ET.SubElement(root, "products")
        for product in self._products:
            prod_elem = ET.SubElement(products_elem, "product")
            ET.SubElement(prod_elem, "id").text = str(product.id())
            ET.SubElement(prod_elem, "name").text = product.name()
            ET.SubElement(prod_elem, "price").text = str(product.price())
            ingredients_list_elem = ET.SubElement(prod_elem, "ingredients")
            for ing in product.ingredients():
                ing_elem = ET.SubElement(ingredients_list_elem, "ingredient")
                ET.SubElement(ing_elem, "ing_id").text = str(self.get_ingredient(ing['name']).id()) 
                ET.SubElement(ing_elem, "name").text = ing['name']
                ET.SubElement(ing_elem, "quantity").text = str(ing['quantity'])
                
        stock_elem = ET.SubElement(root, "stock")
        for item in self._stock:
            item_elem = ET.SubElement(stock_elem, "item")
            ET.SubElement(item_elem, "inv_id").text = str(item.inv_id())
            ET.SubElement(item_elem, "name").text = item.name()
            ET.SubElement(item_elem, "category").text = str(item.category())
            ET.SubElement(item_elem, "quantity").text = str(item.quantity())

        sale_elem = ET.SubElement(root, "sales")
        for sale in self._sales:
            sal_elem = ET.SubElement(sale_elem, "sale")
            ET.SubElement(sal_elem, "product_id").text = str(sale.product_id())
            ET.SubElement(sal_elem, "product_name").text = sale.product_name()
            ET.SubElement(sal_elem, "price").text = str(sale.price())
            ET.SubElement(sal_elem, "quantity").text = str(sale.quantity())
            ET.SubElement(sal_elem, "date").text = str(sale.date())

        expense_type_elem = ET.SubElement(root, "expense_types")
        for expense_type in self._expense_types:
            expense_elem = ET.SubElement(expense_type_elem, "expense_type")
            ET.SubElement(expense_elem, "id").text = str(expense_type.id())
            ET.SubElement(expense_elem, "name").text = expense_type.name()
            ET.SubElement(expense_elem, "default_price").text = str(expense_type.default_price())
            ET.SubElement(expense_elem, "category").text = str(expense_type.category())

        expenses = ET.SubElement(root, "expenses")
        for expense in self._expenses:
            expense_elem = ET.SubElement(expenses, "expense")
            ET.SubElement(expense_elem, "type_id").text = str(expense.type_id())
            ET.SubElement(expense_elem, "name").text = expense.name()
            ET.SubElement(expense_elem, "price").text = str(expense.price())
            ET.SubElement(expense_elem, "category").text = str(expense.category())
            ET.SubElement(expense_elem, "date").text = str(expense.date())
            ET.SubElement(expense_elem, "quantity").text = str(expense.quantity())

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
    
    