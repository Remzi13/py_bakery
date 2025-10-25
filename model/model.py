import xml.etree.ElementTree as ET

class Model:
    
    UNITS_NAME = ['кг', 'грамм', 'литр', 'штуки']

    def __init__(self):
        self.ingredients = []  # Список ингредиентов
        self.products = []     # Список продуктов
        self.load_from_xml()
    
    def __finalize__(self):
        self.save_to_xml()
    
    def get_units(self):
        return self.UNITS_NAME

    def add_ingredient(self, name, unit):   
        self.ingredients.append({'name': name, 'unit': unit})        
    
    def get_ingredient(self, name):
        for ingredient in self.ingredients:
            if ingredient['name'] == name:
                return ingredient
        return None

    def get_ingredients_names(self):
        return [ingredient['name'] for ingredient in self.ingredients]

    def get_ingredients(self):
        return self.ingredients
    
    def add_product(self, name, price, ingredients):        
        self.products.append({'name': name, 'price': price, 'ingredients': ingredients})
    
    def get_products(self):
        return self.products
    
    def save_to_xml(self):
        root = ET.Element("bakery")

        ingredients_elem = ET.SubElement(root, "ingredients")
        for ingredient in self.ingredients:
            ing_elem = ET.SubElement(ingredients_elem, "ingredient")
            ET.SubElement(ing_elem, "name").text = ingredient['name']
            ET.SubElement(ing_elem, "unit").text = str(ingredient['unit'])

        products_elem = ET.SubElement(root, "products")
        for product in self.products:
            prod_elem = ET.SubElement(products_elem, "product")
            ET.SubElement(prod_elem, "name").text = product['name']
            ET.SubElement(prod_elem, "price").text = str(product['price'])
            ingredients_list_elem = ET.SubElement(prod_elem, "ingredients")
            for ing in product['ingredients']:
                ing_elem = ET.SubElement(ingredients_list_elem, "ingredient")
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
                self.ingredients.append({'name': name, 'unit': unit})

            self.products.clear()
            for prod_elem in root.find("products").findall("product"):
                name = prod_elem.find("name").text
                price = float(prod_elem.find("price").text)
                ingredients = []
                for ing_elem in prod_elem.find("ingredients").findall("ingredient"):
                    ing_name = ing_elem.find("name").text
                    quantity = float(ing_elem.find("quantity").text)
                    ingredients.append({'name': ing_name, 'quantity': quantity})
                self.products.append({'name': name, 'price': price, 'ingredients': ingredients})
        except FileNotFoundError:
            pass  # Файл не найден, начинаем с пустых данных
    
    