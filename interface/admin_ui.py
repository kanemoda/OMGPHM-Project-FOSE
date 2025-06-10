from app.db import SessionLocal
from app.models import Ingredient, MenuItem, menuitem_ingredient_table

def run_admin_ui():
    session = SessionLocal()

    print("🧑‍💼 Welcome, Admin!")

    while True:
        print("\n🛠️ Admin Menu:")
        print("1. View & Update Ingredient Stock")
        print("2. Add New Ingredient")
        print("3. Add New Menu Item")
        print("4. Update Menu Item Price")
        print("0. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            view_and_update_stock(session)
        elif choice == "2":
            add_ingredient(session)
        elif choice == "3":
            add_menu_item(session)
        elif choice == "4":
            update_menu_price(session)
        elif choice == "0":
            break
        else:
            print("❌ Invalid choice.")

    session.close()

def view_and_update_stock(session):
    print("\n📦 Ingredients:")
    ingredients = session.query(Ingredient).all()
    for ing in ingredients:
        print(f"{ing.id}. {ing.name} — Stock: {ing.stock_quantity}")

    try:
        ing_id = int(input("Enter ingredient ID to update (0 to cancel): "))
        if ing_id == 0:
            return
        ingredient = session.query(Ingredient).get(ing_id)
        if not ingredient:
            print("❌ Ingredient not found.")
            return
        new_stock = float(input(f"Enter new stock quantity for {ingredient.name}: "))
        ingredient.stock_quantity = new_stock
        session.commit()
        print("✅ Stock updated.")
    except ValueError:
        print("❌ Invalid input.")

def add_ingredient(session):
    name = input("Ingredient name: ").strip()
    try:
        quantity = float(input("Initial stock quantity: "))
        new_ing = Ingredient(name=name, stock_quantity=quantity)
        session.add(new_ing)
        session.commit()
        print(f"✅ Ingredient '{name}' added.")
    except ValueError:
        print("❌ Invalid quantity.")

def add_menu_item(session):
    name = input("Menu item name: ").strip()
    try:
        price = float(input("Price: "))
        new_item = MenuItem(name=name, price=price)
        session.add(new_item)
        session.flush()  # ID almak için

        # Malzeme seç
        ingredients = session.query(Ingredient).all()
        print("\nSelect ingredients for this dish:")
        for ing in ingredients:
            print(f"{ing.id}. {ing.name}")

        print("Enter ingredient ID and amount needed (e.g., 1:2 means ID 1, amount 2).")
        print("Type 'done' when finished.")
        while True:
            entry = input("> ").strip()
            if entry.lower() == "done":
                break
            try:
                ing_id, amount = entry.split(":")
                ing_id = int(ing_id)
                amount = float(amount)
                session.execute(menuitem_ingredient_table.insert().values(
                    menu_item_id=new_item.id,
                    ingredient_id=ing_id,
                    amount_needed=amount
                ))
            except Exception:
                print("⚠️ Invalid format. Use ID:amount.")

        session.commit()
        print(f"✅ Menu item '{name}' added.")
    except ValueError:
        print("❌ Invalid price.")

def update_menu_price(session):
    print("\n🍽️ Menu Items:")
    items = session.query(MenuItem).all()
    for item in items:
        print(f"{item.id}. {item.name} — ${item.price}")

    try:
        item_id = int(input("Enter menu item ID to update (0 to cancel): "))
        if item_id == 0:
            return
        item = session.query(MenuItem).get(item_id)
        if not item:
            print("❌ Item not found.")
            return
        new_price = float(input(f"New price for {item.name}: "))
        item.price = new_price
        session.commit()
        print("✅ Price updated.")
    except ValueError:
        print("❌ Invalid input.")
