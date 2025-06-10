from app.db import SessionLocal
from app.models import Staff, Order, OrderStatus, StaffRole

def run_waiter_ui():
    session = SessionLocal()

    print("🧑‍🍳 Welcome, Waiter!")

    # Garson seçimi
    waiters = session.query(Staff).filter_by(role=StaffRole.waiter).all()
    for w in waiters:
        print(f"{w.id}. {w.name} (Workload: {w.workload})")
    try:
        waiter_id = int(input("Enter your Waiter ID: "))
    except ValueError:
        print("❌ Invalid input.")
        return

    waiter = session.query(Staff).filter_by(id=waiter_id, role=StaffRole.waiter).first()
    if not waiter:
        print("❌ Waiter not found.")
        return

    session.close()

    while True:
        print("\n📋 Waiter Menu:")
        print("1. Confirm new order")
        print("2. Serve ready order & take payment")
        print("0. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            confirm_order(waiter.id)
        elif choice == "2":
            handle_ready_orders(waiter.id)
        elif choice == "0":
            break
        else:
            print("❌ Invalid choice.")


def confirm_order(waiter_id):
    session = SessionLocal()
    from app.models import Order

    orders = session.query(Order).filter_by(waiter_id=waiter_id, status=OrderStatus.pending).all()
    if not orders:
        print("📭 No pending orders assigned to you.")
        session.close()
        return

    print("\n📝 Pending Orders:")
    for order in orders:
        items = ", ".join([item.menu_item.name for item in order.items])
        print(f"Order ID: {order.id} | Table #{order.table.number} | Items: {items}")

    try:
        order_id = int(input("\nEnter Order ID to confirm (or 0 to cancel): "))
    except ValueError:
        print("❌ Invalid input.")
        return

    if order_id == 0:
        print("ℹ️ Cancelled.")
        return

    order = session.query(Order).filter_by(id=order_id, waiter_id=waiter_id, status=OrderStatus.pending).first()
    if not order:
        print("❌ Order not found or already handled.")
        session.close()
        return

    kitchen = session.query(Staff).filter_by(role=StaffRole.kitchen).order_by(Staff.workload).first()
    if not kitchen:
        print("❌ No kitchen staff available.")
        return

    order.status = OrderStatus.confirmed
    order.kitchen_id = kitchen.id

    waiter = session.query(Staff).filter_by(id=waiter_id).first()
    waiter.workload -= 1
    kitchen.workload += 1

    session.commit()
    print(f"✅ Order {order.id} confirmed and sent to kitchen staff: {kitchen.name}")
    session.close()


def handle_ready_orders(waiter_id):
    session = SessionLocal()
    from app.models import MenuItem, Ingredient, menuitem_ingredient_table, OrderItem, Order, PaymentStatus

    orders = session.query(Order).filter_by(waiter_id=waiter_id, status=OrderStatus.ready).all()
    if not orders:
        print("📭 No ready-to-serve orders.")
        session.close()
        return

    print("\n🍽️ Ready Orders:")
    for o in orders:
        item_names = ", ".join([item.menu_item.name for item in o.items])
        print(f"Order ID: {o.id} | Table #{o.table.number} | Items: {item_names}")

    try:
        order_id = int(input("Enter Order ID to serve (or 0 to cancel): "))
    except ValueError:
        print("❌ Invalid input.")
        return

    if order_id == 0:
        print("ℹ️ Cancelled.")
        return

    order = session.query(Order).filter_by(id=order_id, waiter_id=waiter_id, status=OrderStatus.ready).first()
    if not order:
        print("❌ Order not found.")
        return

    for order_item in order.items:
        menu_item = order_item.menu_item
        recipe = session.execute(menuitem_ingredient_table.select().where(
            menuitem_ingredient_table.c.menu_item_id == menu_item.id
        )).fetchall()

        for row in recipe:
            ingredient = session.query(Ingredient).get(row.ingredient_id)
            total_needed = row.amount_needed * order_item.quantity
            if ingredient.stock_quantity < total_needed:
                print(f"⚠️ Not enough stock for {ingredient.name}! Needed: {total_needed}, Available: {ingredient.stock_quantity}")
                session.rollback()
                session.close()
                return
            ingredient.stock_quantity -= total_needed

    order.status = OrderStatus.served
    print("💰 Select payment method:")
    print("1. Cash")
    print("2. Card")
    method = input("Enter 1 or 2: ").strip()
    if method in ("1", "2"):
        order.payment_status = PaymentStatus.paid
    else:
        print("⚠️ Invalid input. Marked as unpaid.")

    session.commit()
    print(f"✅ Order {order.id} served and payment recorded.")

    session.close()
