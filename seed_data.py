import sys
import os
from datetime import datetime, timedelta
import random

# Add current directory to path so we can import sql_model and repositories
sys.path.append(os.getcwd())

from sql_model.model import SQLiteModel

def seed_data():
    model = SQLiteModel()
    
    print("Seeding database with test data...")

    # 1. Add Suppliers
    suppliers = [
        ("Global Flour Co", "John Miller", "555-0101", "sales@globalflour.com", "123 Grain St"),
        ("Dairy Land", "Sarah Cream", "555-0202", "delivery@dairyland.com", "456 Milk Way"),
        ("Packaging Pro", "Ben Box", "555-0303", "orders@packagingpro.com", "789 Wrap Ave"),
        ("Eco Bakery Supplies", "Anna Green", "555-0404", "hello@ecobakery.com", "101 Bio Blvd")
    ]
    
    for name, contact, phone, email, address in suppliers:
        if not model.suppliers().by_name(name):
            model.suppliers().add(name, contact, phone, email, address)
            print(f"Added supplier: {name}")

    # 2. Add Ingredients
    # IngredientsRepository.add also creates StockItem and ExpenseType
    ingredients = [
        ("Premium Flour", "kg"),
        ("White Sugar", "kg"),
        ("Whole Milk", "l"),
        ("Farm Eggs", "pc"),
        ("Dry Yeast", "g"),
        ("Salt", "g"),
        ("Unsalted Butter", "kg"),
        ("Chocolate Chips", "kg"),
        ("Paper Bag", "pc")
    ]
    
    for name, unit in ingredients:
        if not model.ingredients().has(name):
            model.ingredients().add(name, unit)
            print(f"Added ingredient: {name}")

    # 3. Increase Stock (Buying ingredients)
    # We use stock().update(name, delta)
    stock_purchases = [
        ("Premium Flour", 50.0),
        ("White Sugar", 20.0),
        ("Whole Milk", 30.0),
        ("Farm Eggs", 120.0),
        ("Dry Yeast", 500.0),
        ("Salt", 1000.0),
        ("Unsalted Butter", 10.0),
        ("Chocolate Chips", 5.0),
        ("Paper Bag", 200.0)
    ]
    
    for name, qty in stock_purchases:
        try:
            model.stock().update(name, qty)
            print(f"Stocked {qty} of {name}")
        except Exception as e:
            print(f"Error stocking {name}: {e}")

    # 4. Add Products with Recipes
    products = [
        ("Sourdough Loaf", 350, [
            {"name": "Premium Flour", "quantity": 0.5},
            {"name": "Salt", "quantity": 10},
            {"name": "Dry Yeast", "quantity": 5},
            {"name": "Paper Bag", "quantity": 1}
        ]),
        ("Butter Croissant", 120, [
            {"name": "Premium Flour", "quantity": 0.1},
            {"name": "Unsalted Butter", "quantity": 0.050},
            {"name": "Whole Milk", "quantity": 0.02},
            {"name": "White Sugar", "quantity": 0.01},
            {"name": "Paper Bag", "quantity": 1}
        ]),
        ("Chocolate Cookie", 80, [
            {"name": "Premium Flour", "quantity": 0.05},
            {"name": "Unsalted Butter", "quantity": 0.03},
            {"name": "Farm Eggs", "quantity": 0.2},
            {"name": "White Sugar", "quantity": 0.04},
            {"name": "Chocolate Chips", "quantity": 0.02},
            {"name": "Paper Bag", "quantity": 1}
        ])
    ]
    
    for name, price, recipe in products:
        if not model.products().has(name):
            model.products().add(name, price, recipe)
            print(f"Added product: {name}")

    # 5. Add some Expenses (Non-ingredient ones)
    if model.expense_types().len() < 15: # Assuming some types exist already
        expense_categories = ["Utilities", "Other"]
        extra_types = [
            ("Monthly Rent", 50000, "Other"),
            ("Electricity Bill", 8000, "Utilities"),
            ("Water Bill", 2000, "Utilities"),
            ("Internet", 1500, "Other")
        ]
        for name, price, cat in extra_types:
            try:
                model.expense_types().add(name, price, cat)
                print(f"Added expense type: {name}")
            except:
                pass

    # Record some expenses
    extra_expenses = [
        ("Monthly Rent", 50000, 1, None),
        ("Electricity Bill", 8450, 1, None),
        ("Premium Flour", 2500, 1, "Global Flour Co"), # Restocking expense
        ("Unsalted Butter", 4500, 1, "Dairy Land")
    ]
    
    for name, price, qty, supplier in extra_expenses:
        try:
            model.expenses().add(name, price, qty, supplier)
            print(f"Recorded expense: {name}")
        except Exception as e:
            print(f"Error recording expense {name}: {e}")

    # 6. Add Sales (Randomizing dates is hard with current REPO, it uses datetime.now())
    # But we can at least add some quantity
    sales_to_add = [
        ("Sourdough Loaf", 350, 5, 0),
        ("Butter Croissant", 120, 12, 10), # 10% discount
        ("Chocolate Cookie", 80, 20, 0),
        ("Sourdough Loaf", 350, 2, 5),
        ("Butter Croissant", 120, 8, 0)
    ]
    
    for name, price, qty, disc in sales_to_add:
        try:
            model.sales().add(name, price, qty, disc)
            print(f"Recorded sale: {qty}x {name}")
        except Exception as e:
            print(f"Error recording sale {name}: {e}")

    model.close()
    print("Database seeding completed!")

if __name__ == "__main__":
    seed_data()
