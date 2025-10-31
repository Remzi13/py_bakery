
from typing import List, Optional
import xml.etree.ElementTree as ET
import uuid
import model.entities

class ExpenseTypes:

    def __init__(self):        
        self._types: List[model.entities.ExpenseType] = []

    def add(self, name, price, category ):
        self._types.append(model.entities.ExpenseType(name=name, default_price=price, category=category))

    def get(self, name: str) -> Optional[model.entities.ExpenseType]:
        return next((et for et in self._types if et.name == name), None)
    
    def delete(self, name):
        self._types = [expense for expense in self._types if expense.name != name]

    def empty(self) -> bool:
        return len(self._types) == 0
    
    def len(self) -> int:
        return len(self._types)
    
    def data(self):
        return self._types

    def save_to_xml(self, root):
        expense_type_elem = ET.SubElement(root, "expense_types")
        for expense_type in self._types:
            expense_elem = ET.SubElement(expense_type_elem, "expense_type")
            ET.SubElement(expense_elem, "id").text = str(expense_type.id)
            ET.SubElement(expense_elem, "name").text = expense_type.name
            ET.SubElement(expense_elem, "default_price").text = str(expense_type.default_price)
            ET.SubElement(expense_elem, "category").text = str(expense_type.category)

    def load_from_xml(self, root):
        self._types.clear()
        if root.find("expense_types") is not None:
            for expense_type_elem in root.find("expense_types").findall("expense_type"):
                name = expense_type_elem.find("name").text
                default_price = float(expense_type_elem.find("default_price").text)
                category = int(expense_type_elem.find("category").text)
                id = expense_type_elem.find("id").text
                self._types.append(model.entities.ExpenseType(name, default_price, category, uuid.UUID(id)))


class Expenses:

    def __init__(self, types):
        self._expense_types = types
        self._expenses: List[model.entities.Expense] = []

    def add(self, name, price, quantity):
        expense_type = self._expense_types.get(name)
        if not expense_type:
             raise ValueError(f"Тип расхода '{name}' не найден.")

        self._expenses.append(model.entities.Expense(name=name, price=price, category=expense_type.category,
                                            quantity=quantity, type_id=expense_type.id))

    def empty(self):
        return len(self._expenses) == 0
    
    def data(self):
        return self._expenses
    
    def len(self):
        return len(self._expenses)

    def save_to_xml(self, root):
        expenses = ET.SubElement(root, "expenses")
        for expense in self._expenses:
            expense_elem = ET.SubElement(expenses, "expense")
            ET.SubElement(expense_elem, "type_id").text = str(expense.type_id)
            ET.SubElement(expense_elem, "name").text = expense.name
            ET.SubElement(expense_elem, "price").text = str(expense.price)
            ET.SubElement(expense_elem, "category").text = str(expense.category)
            ET.SubElement(expense_elem, "date").text = str(expense.date)
            ET.SubElement(expense_elem, "quantity").text = str(expense.quantity)

    def load_from_xml(self, root):
        self._expenses.clear()
        if root.find("expenses") is not None:
            for expense_elem in root.find("expenses").findall("expense"):
                name = expense_elem.find("name").text
                price = float(expense_elem.find("price").text)
                category = int(expense_elem.find("category").text)
                type_id = expense_elem.find("type_id").text
                date = expense_elem.find("date").text
                quantity = int(expense_elem.find("quantity").text)
                self._expenses.append(model.entities.Expense(name, price, category, quantity, uuid.UUID(type_id), date))
