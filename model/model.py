import xml.etree.ElementTree as ET

import uuid

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
            return f"Product(id={self._id}, name='{self.name}', price={self.price}, ingredients={self.ingredients})"    
        
        def id(self):
            return self._id

        def name(self):
            return self._name
        
        def price(self):
            return self._price
        
        def ingredients(self):
            return self._ingredients


    def __init__(self):
        self.ingredients = []  # Список ингредиентов
        self.products = []     # Список продуктов
        self.load_from_xml()

    def get_units(self):
        return self.UNITS_NAME

    def add_ingredient(self, name, unit):
        self.ingredients.append(Model.Ingredient(name, unit))
    
    def get_ingredient(self, name):
        for ingredient in self.ingredients:
            if ingredient.name() == name:
                return ingredient
        return None

    def get_ingredients_names(self):
        return [ingredient.name() for ingredient in self.ingredients]

    def get_ingredients(self):
        return self.ingredients
    
    def add_product(self, name, price, ingredients):        
        self.products.append(Model.Product(name, price, ingredients))
    
    def delete_product(self, name):
        self.products = [product for product in self.products if product.name() != name]
    
    def get_products(self):
        return self.products
    
    def save_to_xml(self):
        root = ET.Element("bakery")

        ingredients_elem = ET.SubElement(root, "ingredients")
        for ingredient in self.ingredients:
            ing_elem = ET.SubElement(ingredients_elem, "ingredient")
            ET.SubElement(ing_elem, "name").text = ingredient.name()
            ET.SubElement(ing_elem, "unit").text = str(ingredient.unit())
            ET.SubElement(ing_elem, "id").text = str(ingredient.id())

        products_elem = ET.SubElement(root, "products")
        for product in self.products:
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

        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)  # <-- вот эта строка добавляет отступы
        tree.write("bakery_data.xml", encoding="utf-8", xml_declaration=True)

    def load_from_xml(self):
        try:
            tree = ET.parse("bakery_data.xml")
            root = tree.getroot()

            self.ingredients.clear()
            for ing_elem in root.find("ingredients").findall("ingredient"):
                name = ing_elem.find("name").text
                unit = int(ing_elem.find("unit").text)
                id = ing_elem.find("id").text
                self.ingredients.append(Model.Ingredient(name, unit, uuid.UUID(id)))                

            self.products.clear()
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
                #self.products.append({'name': name, 'price': price, 'ingredients': ingredients})
                self.products.append(Model.Product(name, price, ingredients, uuid.UUID(id)))
        except FileNotFoundError:
            pass  # Файл не найден, начинаем с пустых данных
    
    