import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from app.models import Base, Staff, StaffRole, TableModel, Ingredient, MenuItem, Order, OrderStatus

# Test veritabanı
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_test_db():
    """Test veritabanı session'ı"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# ✅ Ana uygulamanın SessionLocal'ini override et
def override_session_local():
    return TestingSessionLocal()

@pytest.fixture(scope="function")
def db_session():
    """Her test için temiz veritabanı"""
    # Veritabanı tablolarını oluştur
    Base.metadata.create_all(bind=engine)
    
    # SessionLocal'i override et
    import main
    original_session_local = main.SessionLocal
    main.SessionLocal = override_session_local
    
    # Test verilerini ekle
    db = TestingSessionLocal()
    
    tables = [TableModel(number=i) for i in range(1, 4)]
    staff = [
        Staff(name="TestWaiter", role=StaffRole.waiter, workload=0),
        Staff(name="TestCook", role=StaffRole.kitchen, workload=0),
        Staff(name="TestAdmin", role=StaffRole.admin, workload=0)
    ]
    ingredients = [
        Ingredient(name="Bread", stock_quantity=10),
        Ingredient(name="Cheese", stock_quantity=10),
        Ingredient(name="Beef", stock_quantity=10)
    ]
    
    db.add_all(tables + staff + ingredients)
    db.commit()
    
    yield db
    
    # Cleanup
    db.close()
    main.SessionLocal = original_session_local
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

class TestHomepage:
    def test_homepage_loads(self):
        response = client.get("/")
        assert response.status_code == 200

class TestLogin:
    def test_login_page_loads(self, db_session):
        response = client.get("/login")
        assert response.status_code == 200
    
    def test_valid_login(self, db_session):
        response = client.post("/login", data={
            "username": "TestWaiter",
            "role": "waiter"
        })
        assert response.status_code == 200
    
    def test_invalid_login(self, db_session):
        response = client.post("/login", data={
            "username": "NonExistent",
            "role": "waiter"
        })
        assert response.status_code == 200
        assert "Invalid credentials" in response.text

class TestCustomerOrder:
    def test_customer_page_loads(self, db_session):
        response = client.get("/customer")
        assert response.status_code == 200
    
    def test_place_order_invalid_table(self, db_session):
        response = client.post("/customer", data={
            "table_number": "999"
        })
        assert response.status_code == 200
        assert "Table not found" in response.text
    
    def test_place_order_no_items(self, db_session):
        response = client.post("/customer", data={
            "table_number": "1"
        })
        assert response.status_code == 200
        assert "You must select at least one menu item" in response.text

class TestWaiterDashboard:
    def test_waiter_dashboard_without_login(self, db_session):
        response = client.get("/waiter/dashboard")
        assert response.status_code == 200

class TestKitchenDashboard:
    def test_kitchen_dashboard_without_login(self, db_session):
        response = client.get("/kitchen/dashboard")
        assert response.status_code == 200

class TestAdminDashboard:
    def test_admin_dashboard_without_login(self, db_session):
        response = client.get("/admin/dashboard")
        assert response.status_code == 200

class TestStockManagement:
    def test_stock_deduction(self, db_session):
        """Stok azalması testi"""
        # İlk stok miktarını al
        ingredient = db_session.query(Ingredient).filter_by(name="Bread").first()
        initial_stock = ingredient.stock_quantity
        
        # Menü öğesi ve tarif oluştur
        menu_item = MenuItem(name="TestBurger", price=5.0)
        db_session.add(menu_item)
        db_session.flush()
        
        from app.models import menuitem_ingredient_table
        db_session.execute(menuitem_ingredient_table.insert().values(
            menu_item_id=menu_item.id,
            ingredient_id=ingredient.id,
            amount_needed=2
        ))
        db_session.commit()
        
        # Sipariş ver
        response = client.post("/customer", data={
            "table_number": "1",
            f"quantity_{menu_item.id}": "1"
        })
        
        assert response.status_code == 200
        
        # Stok kontrolü - Fresh query
        db_session.expire_all()  # Cache'i temizle
        ingredient = db_session.query(Ingredient).filter_by(name="Bread").first()
        assert ingredient.stock_quantity == initial_stock - 2

class TestWorkloadManagement:
    def test_waiter_workload_increases(self, db_session):
        """Waiter workload artış testi"""
        waiter = db_session.query(Staff).filter_by(role=StaffRole.waiter).first()
        initial_workload = waiter.workload
        
        # Yeni ingredient ekle
        ingredient = Ingredient(name="Lettuce", stock_quantity=10)
        db_session.add(ingredient)
        db_session.flush()
        
        # Menü öğesi ve tarif oluştur
        menu_item = MenuItem(name="TestItem", price=5.0)
        db_session.add(menu_item)
        db_session.flush()
        
        from app.models import menuitem_ingredient_table
        db_session.execute(menuitem_ingredient_table.insert().values(
            menu_item_id=menu_item.id,
            ingredient_id=ingredient.id,
            amount_needed=1
        ))
        db_session.commit()
        
        # Sipariş ver
        response = client.post("/customer", data={
            "table_number": "1",
            f"quantity_{menu_item.id}": "1"
        })
        
        assert response.status_code == 200
        
        # Workload kontrolü - Fresh query
        db_session.expire_all()  # Cache'i temizle
        waiter = db_session.query(Staff).filter_by(role=StaffRole.waiter).first()
        assert waiter.workload == initial_workload + 1

class TestDebugEndpoints:
    def test_debug_recipes(self, db_session):
        response = client.get("/debug/recipes")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_debug_waiters(self, db_session):
        response = client.get("/debug/waiters")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_debug_kitchen(self, db_session):
        response = client.get("/debug/kitchen")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_reset_workloads(self, db_session):
        response = client.get("/debug/reset_workloads")
        assert response.status_code == 200
        assert "Workloads reset" in response.json()["msg"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])