from typing import List, Optional
import xml.etree.ElementTree as ET
import uuid
import model.entities

class Stock:

    def __init__(self, model_instance):
        self._model = model_instance
        self._items : List[model.entities.StockItem] = []


    def add(self, name, category, quantity, inv_id):
        self._items.append(model.entities.StockItem(name=name, category=category, quantity=quantity, inv_id=inv_id))

    def delete(self, name):
        self._items = [item for item in self._items if item.name != name]

    def update(self, name, quantity):
        for item in self._items:
            if item.name == name:
                # Inventory - dataclass, но не frozen, можно менять напрямую
                item.quantity += quantity
                return        
        raise KeyError(f"Элемент '{name}' не найден в инвентаре")

    def data(self):
        return self._items
    
    def empty(self) -> bool:
        return len(self._items) == 0