import sys
import os
from sqlalchemy import select

# Add current directory to path
sys.path.append(os.getcwd())

from sql_model.database import SessionLocal, init_db
from sql_model.entities import (
    Unit, StockCategory, ExpenseCategory,
    Supplier, StockItem, Product, ExpenseType,
    product_stock_association
)

def get_or_create(session, model, **kwargs):
    """Helper: gets an object or creates it if it doesn't exist."""
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance

def seed_full_data():
    print("🚀 Starting full database seeding...")
    init_db()  # Ensure tables and default units (kg, l, pc) exist
    db = SessionLocal()

    try:
        # --- 1. REFERENCE DATA ---
        print("📦 Checking reference data...")
        
        # Units (provided by init_db, but we get objects for IDs)
        u_kg = db.query(Unit).filter_by(name='kg').first()
        u_l = db.query(Unit).filter_by(name='l').first()
        u_pc = db.query(Unit).filter_by(name='pc').first()

        # Categories
        cat_raw = get_or_create(db, StockCategory, name='Materials')
        cat_pack = get_or_create(db, StockCategory, name='Packaging')

        exp_cat_raw = get_or_create(db, ExpenseCategory, name='Inventory')
        exp_cat_rent = get_or_create(db, ExpenseCategory, name='Utilities')
        exp_cat_salary = get_or_create(db, ExpenseCategory, name='Salary')

        # --- 2. STOCK ITEMS (Ingredients) ---
        print("🍞 Seeding stock items...")
        
        stock_items_list = [
            {"name": "Wheat Flour", "qty": 150.0, "unit": u_kg, "cat": cat_raw},
            {"name": "Rye Flour", "qty": 50.0, "unit": u_kg, "cat": cat_raw},
            {"name": "Butter 82%", "qty": 20.0, "unit": u_kg, "cat": cat_raw},
            {"name": "Sugar", "qty": 40.0, "unit": u_kg, "cat": cat_raw},
            {"name": "Milk 3.2%", "qty": 50.0, "unit": u_l, "cat": cat_raw},
            {"name": "Eggs C1", "qty": 500.0, "unit": u_pc, "cat": cat_raw},
            {"name": "Dark Chocolate", "qty": 10.0, "unit": u_kg, "cat": cat_raw},
            {"name": "Coffee Beans", "qty": 10.0, "unit": u_kg, "cat": cat_raw},
            {"name": "Paper Bag", "qty": 1000.0, "unit": u_pc, "cat": cat_pack},
            {"name": "Coffee Cup 250ml", "qty": 500.0, "unit": u_pc, "cat": cat_pack},
        ]

        stock_map = {} 
        for item in stock_items_list:
            stock_obj = db.query(StockItem).filter_by(name=item["name"]).first()
            if not stock_obj:
                stock_obj = StockItem(
                    name=item["name"], 
                    quantity=item["qty"], 
                    unit_id=item["unit"].id, 
                    category_id=item["cat"].id
                )
                db.add(stock_obj)
            stock_map[item["name"]] = stock_obj
        
        db.commit()
        for name, obj in stock_map.items():
            db.refresh(obj)

        # --- 3. PRODUCTS (Menu) ---
        print("🥐 Seeding products...")
        
        products_list = [
            {"name": "Classic Croissant", "price": 120.0},
            {"name": "Chocolate Croissant", "price": 160.0},
            {"name": "Borodinsky Bread", "price": 90.0},
            {"name": "Cappuccino 250ml", "price": 150.0},
            {"name": "Espresso", "price": 100.0},
        ]

        product_map = {}
        for p_data in products_list:
            prod = get_or_create(db, Product, name=p_data["name"], price=p_data["price"])
            product_map[p_data["name"]] = prod

        # --- 4. RECIPES (Product-Stock Association) ---
        print("📜 Linking products to stock (Recipes)...")
        
        # Format: "ProductName": [("StockName", quantity_per_unit)]
        recipes = {
            "Classic Croissant": [
                ("Wheat Flour", 0.07), 
                ("Butter 82%", 0.035),
                ("Sugar", 0.01),
                ("Eggs C1", 0.2),
                ("Paper Bag", 1.0)
            ],
            "Chocolate Croissant": [
                ("Wheat Flour", 0.07),
                ("Butter 82%", 0.03),
                ("Dark Chocolate", 0.02),
                ("Paper Bag", 1.0)
            ],
            "Borodinsky Bread": [
                ("Rye Flour", 0.4),
                ("Wheat Flour", 0.1),
                ("Paper Bag", 1.0)
            ],
            "Cappuccino 250ml": [
                ("Coffee Beans", 0.018),
                ("Milk 3.2%", 0.15),
                ("Coffee Cup 250ml", 1.0)
            ]
        }

        # Clear old associations to prevent duplicates
        db.execute(product_stock_association.delete())

        for prod_name, ingredients in recipes.items():
            if prod_name in product_map:
                p_id = product_map[prod_name].id
                for s_name, qty in ingredients:
                    if s_name in stock_map:
                        s_id = stock_map[s_name].id
                        db.execute(product_stock_association.insert().values(
                            product_id=p_id,
                            stock_id=s_id,
                            quantity=qty
                        ))

        # --- 5. EXPENSE TYPES ---
        print("💸 Seeding expense types...")
        expenses = [
            ("Monthly Rent", 50000, exp_cat_rent, False),
            ("Electricity", 7000, exp_cat_rent, False),
            ("Ingredients Restock", 0, exp_cat_raw, True),
            ("Baker Salary", 45000, exp_cat_salary, False),
        ]
        
        for name, price, cat, is_stock in expenses:
            if not db.query(ExpenseType).filter_by(name=name).first():
                db.add(ExpenseType(name=name, default_price=price, category_id=cat.id, stock=is_stock))
        # --- 5. SUPPLIERS ---
        print("🤝 Seeding suppliers...")
        suppliers_list = [
            {
                "name": "Global Grain Co.", 
                "contact_person": "John Doe", 
                "phone": "+1-555-0101", 
                "email": "sales@globalgrain.com",
                "address": "123 Flour Mill St, Buffalo, NY"
            },
            {
                "name": "Dairy Farm Express", 
                "contact_person": "Sarah Miller", 
                "phone": "+1-555-0202", 
                "email": "orders@dairyfarm.com"
            },
            {
                "name": "Eco-Packaging Solutions", 
                "contact_person": "Mike Ross", 
                "phone": "+1-555-0303", 
                "address": "456 Industrial Way, Chicago, IL"
            },
            {
                "name": "Local Energy Corp", 
                "contact_person": "Customer Support", 
                "phone": "8-800-111-22-33"
            }
        ]

        for s_data in suppliers_list:
            get_or_create(db, Supplier, **s_data)
        db.commit()
        print("✅ Database successfully seeded with English data!")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_full_data()