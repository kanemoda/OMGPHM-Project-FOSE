from app.db import SessionLocal
from app.models import TableModel, MenuItem, Order, OrderItem, Staff, StaffRole, OrderStatus

def run_customer_ui():
    session = SessionLocal()

    print("👤 Welcome, Customer!")

    # Masa seç
    tables = session.query(TableModel).all()
    print("Available Tables:")
    for table in tables:
        print(f" - Table #{table.number}")
    try:
        table_number = int(input("Select your table number: "))
    except ValueError:
        print("❌ Invalid input.")
        return

    table = session.query(TableModel).filter_by(number=table_number).first()
    if not table:
        print("❌ Table not found.")
        return

    # Menüden yemek seç
    menu_items = session.query(MenuItem).all()
    print("\n🍽️ Menu:")
    for item in menu_items:
        print(f"{item.id}. {item.name} - ${item.price}")

    selected_items = input("Enter comma-separated menu item IDs (e.g., 1,2): ").split(',')
    order_items = []
    for item_id in selected_items:
        try:
            item = session.query(MenuItem).get(int(item_id.strip()))
            if item:
                order_items.append(item)
            else:
                print(f"⚠️ Item with ID {item_id} not found.")
        except ValueError:
            print(f"⚠️ Invalid ID: {item_id}")

    if not order_items:
        print("❌ No valid items selected.")
        return

    # Garsonlardan en az iş yükü olana ata
    waiter = session.query(Staff).filter_by(role=StaffRole.waiter).order_by(Staff.workload).first()
    if not waiter:
        print("❌ No waiters available.")
        return

    # Sipariş oluştur
    order = Order(
        table_id=table.id,
        waiter_id=waiter.id,
        status=OrderStatus.pending,
    )
    session.add(order)
    session.flush()  # order.id için

    for item in order_items:
        order_item = OrderItem(order_id=order.id, menu_item_id=item.id, quantity=1)
        session.add(order_item)

    # Garson iş yükünü artır
    waiter.workload += 1
    session.commit()

    print(f"\n✅ Order placed successfully! Assigned to waiter: {waiter.name}")
    print(f"📝 Order ID: {order.id} | Items: {', '.join([i.name for i in order_items])}")

    session.close()
