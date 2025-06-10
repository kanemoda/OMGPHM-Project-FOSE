from app.db import SessionLocal
from app.models import Staff, Order, OrderStatus, StaffRole

def run_kitchen_ui():
    session = SessionLocal()

    print("👨‍🍳 Welcome, Kitchen Staff!")

    # Kullanıcıdan personel ID'si al
    kitchen_staff = session.query(Staff).filter_by(role=StaffRole.kitchen).all()
    for k in kitchen_staff:
        print(f"{k.id}. {k.name} (Workload: {k.workload})")
    try:
        kitchen_id = int(input("Enter your Kitchen Staff ID: "))
    except ValueError:
        print("❌ Invalid input.")
        return

    staff = session.query(Staff).filter_by(id=kitchen_id, role=StaffRole.kitchen).first()
    if not staff:
        print("❌ Kitchen staff not found.")
        return

    # Bu mutfak görevlisine atanmış ve status=confirmed olan siparişleri getir
    orders = session.query(Order).filter_by(kitchen_id=staff.id, status=OrderStatus.confirmed).all()
    if not orders:
        print("📭 No orders to prepare.")
        return

    print("\n🍳 Orders to Prepare:")
    for order in orders:
        item_list = ", ".join([item.menu_item.name for item in order.items])
        print(f"Order ID: {order.id} | Table #{order.table.number} | Items: {item_list}")

    try:
        order_id = int(input("\nEnter Order ID to mark as ready (or 0 to cancel): "))
    except ValueError:
        print("❌ Invalid input.")
        return

    if order_id == 0:
        print("ℹ️ Cancelled.")
        return

    order = session.query(Order).filter_by(id=order_id, kitchen_id=staff.id, status=OrderStatus.confirmed).first()
    if not order:
        print("❌ Order not found or already handled.")
        return

    # Siparişi hazırla
    order.status = OrderStatus.ready
    staff.workload -= 1
    session.commit()

    print(f"✅ Order {order.id} marked as READY.")

    session.close()
