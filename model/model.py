
class Model:
    
    UNITS_NAME = ['кг', 'грамм', 'литр', 'штуки']

    def __init__(self):
        self.ingredients = []  # Список ингредиентов

    def get_units(self):
        return self.UNITS_NAME

    def add_ingredient(self, name, unit):   
        self.ingredients.append({'name': name, 'unit': unit})        

    def get_ingredients(self):
        return self.ingredients
    
    