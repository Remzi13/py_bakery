import xml.etree.ElementTree as ET

import uuid
from datetime import datetime

class Model:
    
    UNITS_NAME = ['кг', 'грамм', 'литр', 'штуки']

    

    class Ingredient:
        
        def __init__(self, name: str, unit: str, id: uuid.UUID | None = None):
            self._id = id or uuid.uuid4()  # если id не передан → генерируем новый
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

    class Purchase:

        def __init__(self, name: str, price: int, quantity: int, id: uuid.UUID | None = None):        
            self._id = id or uuid.uuid4()  # если id не передан → генерируем новый
            self._name = name
            self._data = datetime.now().strftime("%Y-%m-%d %H:%M")
            self._price = price
            self._quantity = quantity  # Список ингредиентов с их количеством

        def __repr__(self):
            return f"Purchase(id={self._id}, name='{self.name}', price={self.price}, quantity={self.quantity})"
        
        def id(self):
            return self._id
        
        def name(self):
            return self._name
        
        def price(self):
            return self._price
        
        def quantity(self):
            return self._quantity
        
        def data(self):
            return self._data
    
    class Category:
        INGREDIENT = 1

    class Inventory:

        def __init__(self, name: str, category, quantity: int, id: uuid.UUID):
            self._id = id
            self._name = name
            self._category = category
            self._quantity = quantity

        def __repr__(self):
            return f"Inventory(id={self._id}, name='{self.name}', category={self.category}, quantity={self.quantity})"

        def id(self):
            return self._id 
        
        def name(self): 
            return self._name
        
        def category(self):
            return self._category
        
        def quantity(self):
            return self._quantity
        

    def __init__(self):
        self._ingredients = []
        self._products = []
        self._purchase = []
        self._stock = []

        self.load_from_xml()

    def get_units(self):
        return self.UNITS_NAME

    def add_ingredient(self, name, unit):
        self._ingredients.append(Model.Ingredient(name, unit))
        self.add_inventory(name, Model.Category.INGREDIENT, 0)
    
    def get_ingredient(self, name):
        for ingredient in self._ingredients:
            if ingredient.name() == name:
                return ingredient
        return None

    def get_ingredients_names(self):
        return [ingredient.name() for ingredient in self._ingredients]

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
    
    def get_product_names(self):
        return [product.name() for product in self._products]
    
    def delete_product(self, name):
        self._products = [product for product in self._products if product.name() != name]
    
    def add_purchase(self, name, price, quantity):
        self._purchase.append(Model.Purchase(name, price, quantity))

    def get_purchases(self):
        return self._purchase        

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
        
        purshases_elem = ET.SubElement(root, "purchases")
        for purchase in self._purchase:           
            purch_elem = ET.SubElement(purshases_elem, "purchase")
            ET.SubElement(purch_elem, "id").text = str(purchase.id())
            ET.SubElement(purch_elem, "name").text = purchase.name()
            ET.SubElement(purch_elem, "price").text = str(purchase.price())
            ET.SubElement(purch_elem, "quantity").text = str(purchase.quantity())
            ET.SubElement(purch_elem, "data").text = str(purchase.data())

        stock_elem = ET.SubElement(root, "stock")
        for item in self._stock:
            item_elem = ET.SubElement(stock_elem, "item")
            ET.SubElement(item_elem, "id").text = str(item.id())
            ET.SubElement(item_elem, "name").text = item.name()
            ET.SubElement(item_elem, "category").text = str(item.category())
            ET.SubElement(item_elem, "quantity").text = str(item.quantity())

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)  # <-- вот эта строка добавляет отступы
        tree.write("bakery_data.xml", encoding="utf-8", xml_declaration=True)

    def load_from_xml(self):
        try:
            tree = ET.parse("bakery_data.xml")
            root = tree.getroot()

            self._ingredients.clear()
            for ing_elem in root.find("ingredients").findall("ingredient"):
                name = ing_elem.find("name").text
                unit = int(ing_elem.find("unit").text)
                id = ing_elem.find("id").text
                self._ingredients.append(Model.Ingredient(name, unit, uuid.UUID(id))) 

            self._products.clear()
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

            self._purchase.clear()
            if root.find("purchases") is not None:
                for purch_elem in root.find("purchases").findall("purchase"):
                    name = purch_elem.find("name").text
                    price = float(purch_elem.find("price").text)
                    quantity = int(purch_elem.find("quantity").text)
                    id = purch_elem.find("id").text
                    self._purchase.append(Model.Purchase(name, price, quantity, uuid.UUID(id)))
        
            self._stock.clear()
            if root.find("stock") is not None:
                for item_elem in root.find("stock").findall("item"):
                    name = item_elem.find("name").text
                    category = int(item_elem.find("category").text)
                    quantity = int(item_elem.find("quantity").text)
                    id = item_elem.find("id").text
                    self._stock.append(Model.Inventory(name, category, quantity, uuid.UUID(id)))    

        except FileNotFoundError:
            pass  # Файл не найден, начинаем с пустых данных
    
    