from typing import List, Optional
import xml.etree.ElementTree as ET
import uuid
import model.entities

class Stock:

    def __init__(self):
        self._items : List[model.entities.StockItem] = []

    def add(self, name : str, category : model.entities.StockCategory, quantity : float, unit : model.entities.Unit):
        self._items.append(model.entities.StockItem(name=name, category=category, quantity=quantity, unit=unit))

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
    
    def len(self) -> int:
        return len(self._items)
    
    def save_to_xml(self, root):
        stock_elem = ET.SubElement(root, "stock")
        for item in self._items:
            item_elem = ET.SubElement(stock_elem, "item")
            ET.SubElement(item_elem, "id").text = str(item.id)
            ET.SubElement(item_elem, "name").text = item.name
            ET.SubElement(item_elem, "category").text = str(item.category)
            ET.SubElement(item_elem, "quantity").text = str(item.quantity)
            ET.SubElement(item_elem, "unit").text = str(item.unit)

    def load_from_xml(self, root):
        self._items.clear()
        if root.find("stock") is not None:
            for item in root.find("stock").findall("item"):
                name = item.find("name").text
                category = int(item.find("category").text)
                quantity = float(item.find("quantity").text)
                id = item.find("id").text
                unit = int(item.find("unit").text)
                self._items.append(model.entities.StockItem(name=name, category=category, quantity=quantity, unit=unit, id = uuid.UUID(id)))


