from typing import List, Optional
import xml.etree.ElementTree as ET
import uuid
import model.entities

class Ingredients:

    def __init__(self, model_instance):
        self._model = model_instance
        self._ingredients: List[model.entities.Ingredient] = []

    def by_name(self, name: str) -> Optional[model.entities.Ingredient]:
        return next((i for i in self._ingredients if i.name == name), None)

    def by_id(self, id: uuid.UUID) -> Optional[model.entities.Ingredient]:
        return next((i for i in self._ingredients if i.id == id), None)

    def len(self):
        return len(self._ingredients)
    
    def data(self):
        return self._ingredients
    
    def empty(self) -> bool:
        return len(self._ingredients) == 0
    
    def names(self):
        return [i.name for i in self._ingredients]

    def add(self, name, unit: int):
        ing = model.entities.Ingredient(name=name, unit=unit)
        self._ingredients.append(ing)
        self._model.add_inventory(name, model.entities.Category.INGREDIENT, 0, ing.id)
        self._model.add_expense_type(name, 100, model.entities.Category.INGREDIENT)

    def delete(self, name):
        ingredient = self.by_name(name)
        products = self._model.get_products()
        for product in products:
            for ing in product.ingredients:
                if ing['name'] == name:
                    raise ValueError(f"Ингредиент '{name}' используется в продукте '{product.name}'. Удаление невозможно.")
        if ingredient:
            self._ingredients = [ing for ing in self._ingredients if ing.name != name]
            # Удаляем связанные записи в инвентаре и типах расходов
            self._model.delete_inventory(name) # [item for item in self._stock if item.inv_id != ingredient.id]
            self._model.delete_expense_type(name) # [et for et in self._expense_types if et.name != name]

    def save_to_xml(self, root : ET.ElementTree):

        ingredients_elem = ET.SubElement(root, "ingredients")
        for ingredient in self._ingredients:
            ing_elem = ET.SubElement(ingredients_elem, "ingredient")
            ET.SubElement(ing_elem, "name").text = ingredient.name
            ET.SubElement(ing_elem, "unit").text = str(ingredient.unit)
            ET.SubElement(ing_elem, "id").text = str(ingredient.id)

    def load_from_xml(self, root : ET.ElementTree):
        self._ingredients.clear()
        if root.find("ingredients") is not None:
            for ing_elem in root.find("ingredients").findall("ingredient"):
                name = ing_elem.find("name").text
                unit = int(ing_elem.find("unit").text)
                id = ing_elem.find("id").text
                self._ingredients.append(model.entities.Ingredient(name, unit, uuid.UUID(id)))
