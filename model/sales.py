from typing import List, Optional
import xml.etree.ElementTree as ET
import uuid
import model.entities

class Sales:

    def __init__(self, stock, products):
        self._stock = stock
        self._products = products
        self._sales : List[model.entities.Sale] = []

    def add(self, name, price, quantity, discount):
        product = self._products.by_name(name)

        if product:
            for i in product.ingredients:
                # Используем прямой доступ к ключам словаря i['name'], i['quantity']
                # (В идеале ingredients должны быть dataclass'ами, но для совместимости оставим так)
                self._stock.update(i['name'], -i['quantity'] * quantity)

            self._sales.append(model.entities.Sale(product_name=name, price=price, quantity=quantity, discount=discount, product_id=product.id))
        else:            
            raise ValueError(f"Продукт '{name}' не найден")

    def data(self):
        return self._sales
    
    def empty(self) -> bool:        
        return len(self._sales) == 0
    
    def len(self) -> int:
        return len(self._sales)
    
    def save_to_xml(self, root):

        sale_elem = ET.SubElement(root, "sales")
        for sale in self._sales:
            sal_elem = ET.SubElement(sale_elem, "sale")
            ET.SubElement(sal_elem, "product_id").text = str(sale.product_id)
            ET.SubElement(sal_elem, "product_name").text = sale.product_name
            ET.SubElement(sal_elem, "price").text = str(sale.price)
            ET.SubElement(sal_elem, "quantity").text = str(sale.quantity)
            ET.SubElement(sal_elem, "discount").text = str(sale.discount)
            ET.SubElement(sal_elem, "date").text = str(sale.date)

    def load_from_xml(self, root):
        self._sales.clear()
        if root.find("sales") is not None:  
            for sale_elem in root.find("sales").findall("sale"):
                product_name = sale_elem.find("product_name").text
                price = float(sale_elem.find("price").text)
                quantity = int(sale_elem.find("quantity").text)
                id = sale_elem.find("product_id").text
                date = sale_elem.find("date").text
                discount = int(sale_elem.find("discount").text)
                self._sales.append(model.entities.Sale(product_name=product_name, price=price, quantity=quantity, discount=discount, product_id=uuid.UUID(id), date=date))
