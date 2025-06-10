from app.db import SessionLocal, init_db
from app.models import Staff, StaffRole, TableModel, Ingredient, MenuItem, menuitem_ingredient_table
from sqlalchemy.exc import IntegrityError

def seed_tables(session):
    tables = [TableModel(number=i) for i in range(1, 6)]  # 1–5 arası masa
    session.add_all(tables)

def seed_staff(session):
    waiters = [Staff(name=f"Waiter{i}", role=StaffRole.waiter) for i in range(1, 4)]
    kitchen = [Staff(name=f"Cook{i}", role=StaffRole.kitchen) for i in range(1, 3)]
    session.add_all(waiters + kitchen)

def seed_ingredients(session):
    ingredients = [
        Ingredient(name="Bread", stock_quantity=50),
        Ingredient(name="Cheese", stock_quantity=30),
        Ingredient(name="Beef", stock_quantity=20),
        Ingredient(name="Flour", stock_quantity=50),
        Ingredient(name="Tomato", stock_quantity=40),
        Ingredient(name="Potato", stock_quantity=60),
        Ingredient(name="Oil", stock_quantity=30),
    ]
    session.add_all(ingredients)

def seed_menu(session):
    # MenuItem'ları oluştur
    burger = MenuItem(name="Cheeseburger", price=9.99)
    pizza = MenuItem(name="Margherita Pizza", price=12.50)
    fries = MenuItem(name="Fries", price=4.50)
    session.add_all([burger, pizza, fries])
    session.flush()  # id’ler oluşsun

    # Menü – Malzeme eşleşmeleri
    ingredient_map = {i.name: i for i in session.query(Ingredient).all()}

    recipe_data = {
        burger.id: [("Bread", 1), ("Cheese", 1), ("Beef", 1)],
        pizza.id: [("Flour", 2), ("Cheese", 1), ("Tomato", 2)],
        fries.id: [("Potato", 3), ("Oil", 1)],
    }

    for menu_id, ingredients in recipe_data.items():
        for ing_name, amount in ingredients:
            ing = ingredient_map[ing_name]
            session.execute(menuitem_ingredient_table.insert().values(
                menu_item_id=menu_id,
                ingredient_id=ing.id,
                amount_needed=amount
            ))

def seed_all():
    init_db()
    session = SessionLocal()
    try:
        seed_tables(session)
        seed_staff(session)
        seed_ingredients(session)
        seed_menu(session)
        session.commit()
        print("🌱 Seeding complete!")
    except IntegrityError:
        session.rollback()
        print("⚠️ Data already seeded or duplicate entries.")
    finally:
        session.close()

if __name__ == "__main__":
    seed_all()
