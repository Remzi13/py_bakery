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
            {"name": "Brasno",    "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Rye Flour",       "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Maslac 82%",      "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Kvasac suvi",       "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Secer",           "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Jaja M",         "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Luk mladi",       "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Krompir",          "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Pavlaka za kuvanje",       "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Pileci batak I karabatak bez kosti",          "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Sampinjoni",     "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Junece mleveno meso 7",  "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Paradaiz seckani Lidl",  "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Poli viršla",    "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Scrob kukuruzni",     "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Sir svezi",  "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Kisela pavlaka 20",  "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Cinnamon",        "qty": 1000.0,   "unit": u_kg, "rep_unit": u_g, "cat": cat_raw},
            {"name": "Mleko 2,8",       "qty": 1000.0,   "unit": u_l,  "rep_unit": u_ml, "cat": cat_raw},
            {"name": "Voda",            "qty": 1000.0,   "unit": u_l,  "rep_unit": u_ml, "cat": cat_raw},   
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
            {"name": "Pies Luk mladi and eggs", "price": 130.0},
            {"name": "Pies krompir", "price": 130.0},            
            {"name": "Pies beef", "price": 170.0},              
            {"name": "Cinamon", "price": 150},            
            {"name": "Pies with cabbage and egg", "price": 100.0}, # Пирожки с капустой и яйцом
            {"name": "Pies with green onions and egg", "price": 100.0}, # Пирожки с зеленым луком и яйцом
            {"name": "Pies with Krompir", "price": 100.0}, # Пирожки с картофелем
            {"name": "Pies with chicken and Sampinjoni", "price": 150.0}, # Пирожки с курицей и грибами
            {"name": "Pies with beef and spinach", "price": 150.0}, # Пирожки с говядиной и шпинатом
            {"name": "Hot dog mini", "price": 120.0},
            {"name": "Pies with red fish, Sir svezi and parsley", "price": 220.0}, # Пирожки с красной рыбой, творожным сыром и зеленью
            {"name": "Pies with red fish and egg", "price": 150.0}, # Пирожки с красной рыбой и яйцом
            {"name": "Pies with cheese", "price": 150.0}, # Плетенки с сыром
            {"name": "Pies with Krompir and cheese", "price": 150.0}, # Плетенки с картофелем и сыром
            {"name": "Pies with Sir svezi", "price": 150.0},
            {"name": "Vengerka with Sir svezi", "price": 260.0}, # Венгерская ватрушка с творогом
            {"name": "Moskovskaya plushka", "price": 100.0}, # Московская плюшка
            {"name": "Pletenica with apples", "price": 150.0}, # Плетеница с яблоком
            {"name": "Kolach boravina", "price": 150.0}, # Колач боравница
            {"name": "Kolpch limun", "price": 150.0}, # Колпч лимун
            {"name": "Pies with cherries", "price": 100.0}, # Пирожки с вишней
            {"name": "Pies with blackberry", "price": 120.0}, # Пирожки с малиной
            {"name": "Tvorog", "price": 250.0}, # Творожная запеканка
            {"name": "Sharlotka", "price": 150.0}, # Шарлотка
            {"name": "Pletenka lemon", "price": 150.0}, # Плетенка лимонная
            {"name": "Pletenka chocolate", "price": 100.0}, # Плетенка с шоколадом и заварным кремом
            {"name": "Pletenka poppy seed", "price": 150.0}, # Плетенка с маком
            {"name": "Pletenka cinnamon", "price": 150.0}, # Плетенка корица
            {"name": "Rom bab", "price": 200.0}, # Ром баба
            {"name": "Oblepikhoviy limonad", "price": 200.0}, # Облепиховый лимонад
            {"name": "Kurabie", "price": 50.0}, # Курабье
            {"name": "Pesochnoe koltso", "price": 120.0}, # Песочное кольцо
            {"name": "Pies with apples", "price": 100.0}, # Пирожки с яблоками
            {"name": "Pies with jam", "price": 100.0}, # Пирожки с повидлом
            {"name": "Fruit and berry mix", "price": 100.0}, # Фруктово-ягодный микс
        ]

        product_map = {}
        for p_data in products_list:
            prod = get_or_create(db, Product, name=p_data["name"], price=p_data["price"])
            product_map[p_data["name"]] = prod

        # --- 4. RECIPES (Product-Stock Association) ---
        print("📜 Linking products to stock (Recipes)...")
        
        # Data calculated from your spreadsheet (summing dough + filling where needed)
        recipes = {                        
            "Pies Luk mladi and eggs": [
                ("Brasno", 0.01899), 
                ("Jaja M", 0.00696 + 0.02232), 
                ("Kvasac suvi", 0.00019),
                ("Maslac 82%", 0.00188), 
                ("Mleko 2,8", 0.00314 + 0.00304),
                ("Secer", 0.00251),
                ("Vodar", 0.00633),
                ("Luk mladi", 0.01964)
            ],
            "Pies krompir": [
                ("Brasno", 0.01899), 
                ("Jaja M", 0.00696),
                ("Kvasac suvi", 0.00019),
                ("Maslac 82%", 0.00188 + 0.00283),
                ("Mleko 2,8", 0.00314 + 0.00452),
                ("Secer", 0.00251),
                ("Vodar", 0.00633),
                ("Krompir", 0.03765)
            ],
            "Pies Pileci batak I karabatak bez kosti and Sampinjoni": [
                ("Brasno", 0.01899),
                ("Jaja M", 0.00696),
                ("Kvasac suvi", 0.00019),
                ("Maslac 82%", 0.00188),
                ("Mleko 2,8", 0.00314),
                ("Secer", 0.00251),
                ("Vodar", 0.00633),
                ("Pavlaka za kuvanje", 0.00569),
                ("Pileci batak I karabatak bez kosti", 0.02112),
                ("Sampinjoni", 0.01819)
            ],
            "Pies beef": [
                ("Brasno", 0.01899), 
                ("Jaja M", 0.00696),
                ("Kvasac suvi", 0.00019),
                ("Maslac 82%", 0.00188),
                ("Mleko 2,8", 0.00314),
                ("Secer", 0.00251),
                ("Vodar", 0.00633),
                ("Junece mleveno meso 7", 0.03441),
                ("Paradaiz seckani Lidl", 0.01059)
            ],
            "Hot dog mini": [
                ("Brasno", 0.01899),
                ("Jaja M", 0.00696),
                ("Kvasac suvi", 0.00019),
                ("Maslac 82%", 0.00188),
                ("Mleko 2,8", 0.00314),
                ("Secer", 0.00251),
                ("Vodar", 0.00633),
                ("Poli viršla", 0.033)
            ],
            "Tvorog":[
                ("Brasno", 0.03322),
                ("Jaja M", 0.01217 + 0.00444),
                ("Kvasac suvi", 0.00034),
                ("Maslac 82%", 0.0033),
                ("Mleko 2,8", 0.0055),
                ("Secer", 0.0044 + 0.00901),
                ("Vodar", 0.01107),
                ("Scrob kukuruzni", 0.006),
                ("Sir svezi", 0.06004),
                ("Kisela pavlaka 20", 0.01051)
            ],
            "Cinamon": [
                ("Brasno", 0.03322),
                ("Jaja M", 0.01217),
                ("Kvasac suvi", 0.00034),
                ("Maslac 82%", 0.0033 + 0.00465),
                ("Mleko 2,8", 0.0055),
                ("Secer", 0.0044 + 0.0155),
                ("Vodar", 0.01107),
                ("Cinnamon", 0.00155)
            ],
            "Pies with cabbage and egg": [
                ("Brasno", 0.01899)                
            ],
            "Pies with green onions and egg": [
                ("Brasno", 0.01899)                
            ],
            "Pies with Krompir": [
                ("Brasno", 0.01899)                
            ],
            "Pies with chicken and Sampinjoni": [
                ("Brasno", 0.01899)                
            ],
            "Pies with beef and spinach": [
                ("Brasno", 0.01899)                
            ],
            "Pies with red fish, Sir svezi and parsley": [
                ("Brasno", 0.01899)                
            ],
            "Pies with red fish and egg": [
                ("Brasno", 0.01899)                
            ],
            "Pies with cheese": [
                ("Brasno", 0.01899)                
            ],
            "Pies with Krompir and cheese": [
                ("Brasno", 0.01899)                
            ],
            "Pies with Sir svezi": [
                ("Brasno", 0.01899)                
            ],
            "Cinamon": [
                ("Brasno", 0.03322)                
            ],
            "Pies with red fish and egg": [
                ("Brasno", 0.01899)                
            ],
            "Pies with cheese": [
                ("Brasno", 0.01899)                
            ],
            "Pies with Krompir and cheese": [
                ("Brasno", 0.01899)                
            ],
            "Pies with Sir svezi": [
                ("Brasno", 0.01899)                
            ],                
            "Pletenka poppy seed": [
                ("Brasno", 0.03322)                
            ],
            "Pletenka cinnamon": [
                ("Brasno", 0.03322)      
            ],
            "Rom bab": [
                ("Brasno", 0.03322)
            ],
            "Oblepikhoviy limonad": [
                ("Brasno", 0.03322)
            ],
            "Kurabie": [
                ("Brasno", 0.03322)
            ],
            "Pesochnoe koltso": [
                ("Brasno", 0.03322)
            ],
            "Pies with apples": [
                ("Brasno", 0.01899)
            ],
            "Pies with jam": [
                ("Brasno", 0.01899)
            ],
            "Fruit and berry mix": [
                ("Brasno", 0.03322)
            ],
            "Sharlotka": [
                ("Brasno", 0.03322)
            ],
            "Pletenka lemon": [
                ("Brasno", 0.03322)  
            ],
            "Pletenka chocolate": [
                ("Brasno", 0.03322)
            ],
            "Vengerka with Sir svezi": [
                ("Brasno", 0.01899)
            ],
            "Moskovskaya plushka": [
                ("Brasno", 0.03322)
            ],
            "Pletenica with apples": [
                ("Brasno", 0.03322)
            ],
            "Kolach boravina": [
                ("Brasno", 0.03322)
            ],
            "Kolpch limun": [
                ("Brasno", 0.03322)
            ],
            "Pies with cherries": [
                ("Brasno", 0.01899)
            ],
            "Pies with blackberry": [
                ("Brasno", 0.01899)
            ],
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
                            con_factor = 0.001
                            quantity = qty  * 1000
                            db.add(ProductRecipe(product_id=p_id, stock_id=s_id, quantity=quantity , conversion_factor=con_factor, recipe_unit_id=r_id ))

        # --- 6. SUPPLIERS ---
        print("🤝 Seeding suppliers...")
        suppliers_list = [
            {"name": "Maxi", "contact_person": "John Doe", "phone": "+1-555-0101", "email": "none@globalgrain.com"},
            {"name": "Lidl (sava)", "contact_person": "Sarah Miller", "phone": "+1-555-0202", "email": "none@globalgrain.com"},
            {"name": "Metro Zemun ", "contact_person": "Mike Ross", "phone": "+1-555-0303", "email": "none@globalgrain.com"},
            {"name": "Metro (delivery)", "contact_person": "Customer Support", "phone": "8-800-111-22-33", "email": "none@globalgrain.com"},
            {"name": "Super Vero", "contact_person": "Anna Smith", "phone": "+1-555-0404", "email": "mail@mail.com"},
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