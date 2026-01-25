import sys
import os
from sqlalchemy import select

# Add current directory to path
sys.path.append(os.getcwd())

from sql_model.database import SessionLocal, init_db
from sql_model.entities import (
    Unit, StockCategory, ExpenseCategory,
    Supplier, StockItem, Product, ExpenseType,
    ProductRecipe
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
    init_db()  # Ensure tables and default units exist
    db = SessionLocal()

    try:
        # --- 1. REFERENCE DATA ---
        print("📦 Checking reference data...")
        
        u_kg = db.query(Unit).filter_by(name='kg').first()
        u_g = db.query(Unit).filter_by(name='g').first()
        u_l = db.query(Unit).filter_by(name='l').first()
        u_ml = db.query(Unit).filter_by(name='ml').first()
        u_pc = db.query(Unit).filter_by(name='pc').first()

        cat_raw = get_or_create(db, StockCategory, name='Materials')
        cat_pack = get_or_create(db, StockCategory, name='Packaging')

        exp_cat_raw = get_or_create(db, ExpenseCategory, name='Inventory')
        exp_cat_rent = get_or_create(db, ExpenseCategory, name='Utilities')
        exp_cat_salary = get_or_create(db, ExpenseCategory, name='Salary')

        # --- 2. STOCK ITEMS (Ingredients) ---
        print("🍞 Seeding stock items...")
        
        # Combined existing items and new items from the image
        stock_items_list = [            
            {"name": "Flour DANUBI",    "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw}, # New
            {"name": "Rye Flour",       "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Butter 82%",      "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Yeast dry",       "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},     # New
            {"name": "Sugar",           "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},            
            {"name": "Eggs C1",         "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Scallions",       "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},   # New
            {"name": "Potato",          "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},      # New
            {"name": "Cream 20%",       "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},   # New
            {"name": "Chiken",          "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},      # New
            {"name": "Champignons",     "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw}, # New
            {"name": "Beef minced 7%",  "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw}, # New
            {"name": "Tomato chopped",  "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw}, # New
            {"name": "Sausage mini",    "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},   # New         
            {"name": "Corn starch",     "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Cottage cheese",  "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Sour cream 20%",  "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Cinnamon",        "qty": 100.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Milk 3.2%",       "qty": 100.0,   "unit": u_l,  "rep_unit": u_ml, "cat": cat_raw},
            {"name": "Wate",            "qty": 100.0,   "unit": u_l,  "rep_unit": u_ml, "cat": cat_raw},   
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

            if not db.query(ExpenseType).filter_by(name=item["name"]).first():
                db.add(ExpenseType(name=item["name"], default_price=100, category_id=item["cat"].id, unit_id=item["unit"].id, stock=True))
        
        db.commit()

        # --- 3. PRODUCTS (Menu) ---
        print("🥐 Seeding products...")
        
        products_list = [            
            {"name": "Pies scallions and eggs", "price": 130.0},
            {"name": "Pies krompir", "price": 130.0},
            {"name": "Pies chiken and champignons", "price": 170.0},
            {"name": "Pies beef", "price": 170.0},  
            {"name": "Tvorog", "price": 260.0},
            {"name": "Cinamon", "price": 150},
        ]

        product_map = {}
        for p_data in products_list:
            prod = get_or_create(db, Product, name=p_data["name"], price=p_data["price"])
            product_map[p_data["name"]] = prod

        # --- 4. RECIPES (Product-Stock Association) ---
        print("📜 Linking products to stock (Recipes)...")
        
        # Data calculated from your spreadsheet (summing dough + filling where needed)
        recipes = {                        
            "Pies scallions and eggs": [
                ("Flour DANUBI", 0.01899), 
                ("Eggs C1", 0.00696 + 0.02232), 
                ("Yeast dry", 0.00019),
                ("Butter 82%", 0.00188), 
                ("Milk 3.2%", 0.00314 + 0.00304),
                ("Sugar", 0.00251),
                ("Water", 0.00633),
                ("Scallions", 0.01964)
            ],
            "Pies krompir": [
                ("Flour DANUBI", 0.01899), 
                ("Eggs C1", 0.00696),
                ("Yeast dry", 0.00019),
                ("Butter 82%", 0.00188 + 0.00283),
                ("Milk 3.2%", 0.00314 + 0.00452),
                ("Sugar", 0.00251),
                ("Water", 0.00633),
                ("Potato", 0.03765)
            ],
            "Pies chiken and champignons": [
                ("Flour DANUBI", 0.01899),
                ("Eggs C1", 0.00696),
                ("Yeast dry", 0.00019),
                ("Butter 82%", 0.00188),
                ("Milk 3.2%", 0.00314),
                ("Sugar", 0.00251),
                ("Water", 0.00633),
                ("Cream 20%", 0.00569),
                ("Chiken", 0.02112),
                ("Champignons", 0.01819)
            ],
            "Pies beef": [
                ("Flour DANUBI", 0.01899), 
                ("Eggs C1", 0.00696),
                ("Yeast dry", 0.00019),
                ("Butter 82%", 0.00188),
                ("Milk 3.2%", 0.00314),
                ("Sugar", 0.00251),
                ("Water", 0.00633),
                ("Beef minced 7%", 0.03441),
                ("Tomato chopped", 0.01059)
            ],
            "Hot dog mini": [
                ("Flour DANUBI", 0.01899),
                ("Eggs C1", 0.00696),
                ("Yeast dry", 0.00019),
                ("Butter 82%", 0.00188),
                ("Milk 3.2%", 0.00314),
                ("Sugar", 0.00251),
                ("Water", 0.00633),
                ("Sausage mini", 0.033)
            ],
            "Tvorog":[
                ("Flour DANUBI", 0.03322),
                ("Eggs C1", 0.01217 + 0.00444),
                ("Yeast dry", 0.00034),
                ("Butter 82%", 0.0033),
                ("Milk 3.2%", 0.0055),
                ("Sugar", 0.0044 + 0.00901),
                ("Water", 0.01107),
                ("Corn starch", 0.006),
                ("Cottage cheese", 0.06004),
                ("Sour cream 20%", 0.01051)
            ],
            "Cinamon": [
                ("Flour DANUBI", 0.03322),
                ("Eggs C1", 0.01217),
                ("Yeast dry", 0.00034),
                ("Butter 82%", 0.0033 + 0.00465),
                ("Milk 3.2%", 0.0055),
                ("Sugar", 0.0044 + 0.0155),
                ("Water", 0.01107),
                ("Cinnamon", 0.00155)
            ]
        }

        for prod_name, ingredients in recipes.items():
            if prod_name in product_map:
                p_id = product_map[prod_name].id
                for s_name, qty in ingredients:
                    if s_name in stock_map:
                        s_id = stock_map[s_name].id
                        r_id = 0
                        for item in stock_items_list:
                            if item["name"] == s_name:
                                r_id = item["rep_unit"].id
                        # Check if recipe link already exists to prevent duplicates
                        exists = db.query(ProductRecipe).filter_by(product_id=p_id, stock_id=s_id).first()
                        if not exists:
                            con_factor = 1000
                            db.add(ProductRecipe(product_id=p_id, stock_id=s_id, quantity=qty, conversion_factor=con_factor, recipe_unit_id=r_id ))

        # --- 6. SUPPLIERS ---
        print("🤝 Seeding suppliers...")
        suppliers_list = [
            {"name": "Maxi", "contact_person": "John Doe", "phone": "+1-555-0101", "email": "none@globalgrain.com"},
            {"name": "Lidl (sava)", "contact_person": "Sarah Miller", "phone": "+1-555-0202", "email": "none@globalgrain.com"},
            {"name": "Metro Zemun ", "contact_person": "Mike Ross", "phone": "+1-555-0303", "email": "none@globalgrain.com"},
            {"name": "Metro (delivery)", "contact_person": "Customer Support", "phone": "8-800-111-22-33", "email": "none@globalgrain.com"}
        ]

        for s_data in suppliers_list:
            get_or_create(db, Supplier, **s_data)

        db.commit()
        print("✅ Database successfully seeded with original and image data!")

    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_full_data()