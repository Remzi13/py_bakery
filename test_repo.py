import sqlite3
from repositories.orders import OrdersRepository
from types import SimpleNamespace

def test():
    conn = sqlite3.connect('bakery_management.db')
    conn.row_factory = sqlite3.Row
    repo = OrdersRepository(conn, SimpleNamespace(products=lambda: SimpleNamespace(by_id=lambda x: SimpleNamespace(id=x, name="Test", price=10))))
    
    try:
        print("Testing data()...")
        orders = repo.data()
        print(f"Found {len(orders)} orders")
        for o in orders:
            print(f"Order #{o.id}: {len(o.items)} items")
            for item in o.items:
                print(f"  Item: {item}")
                
        print("\nTesting get_pending()...")
        pending = repo.get_pending()
        print(f"Found {len(pending)} pending orders")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test()
