from typing import List, Optional
import xml.etree.ElementTree as ET
import uuid
import model.entities

from typing import List, Dict

class Products:

    def __init__(self, ingredients):
        self._ingredients = ingredients
        self._products: List[model.entities.Product] = []

    def add(self, name, price, ingredients: List[Dict]):
        new_product = model.entities.Product(name=name, price=price, ingredients=ingredients)

        # Логика обновления продукта, если он уже существует
        for i, product in enumerate(self._products):
            if product.name == name:
                self._products[i] = new_product
                return

        self._products.append(new_product)

    def delete(self, name):
        self._products = [product for product in self._products if product.name != name]

    def by_name(self, name: str) -> Optional[model.entities.Product]:
        return next((i for i in self._products if i.name == name), None)
    
    def has(self, name : str) -> bool:
        return self.by_name(name) is not None

    def empty(self) -> bool:
        return len(self._products) == 0
    
    def len(self) -> int:
        return len(self._products)
    
    def names(self):
        return [i.name for i in self._products]
    
    def data(self):
        return self._products
    
    def save_to_xml(self, root : ET.ElementTree):
        products_elem = ET.SubElement(root, "products")
        for product in self._products:
            prod_elem = ET.SubElement(products_elem, "product")
            ET.SubElement(prod_elem, "id").text = str(product.id)
            ET.SubElement(prod_elem, "name").text = product.name
            ET.SubElement(prod_elem, "price").text = str(product.price)
            ingredients_list_elem = ET.SubElement(prod_elem, "ingredients")
            for ing in product.ingredients:
                ing_elem = ET.SubElement(ingredients_list_elem, "ingredient")
                ET.SubElement(ing_elem, "ing_id").text = str(self._ingredients.by_name(ing['name']).id) 
                ET.SubElement(ing_elem, "name").text = ing['name']
                ET.SubElement(ing_elem, "quantity").text = str(ing['quantity'])

    def load_from_xml(self, root : ET.ElementTree):
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
                self._products.append(model.entities.Product(name, price, ingredients, uuid.UUID(id)))