from fastapi import FastAPI, Request, Form, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from typing import List
from sqlalchemy.orm import joinedload

from app.db import SessionLocal
from app.models import (
    Staff, StaffRole, TableModel, MenuItem,
    Order, OrderItem, OrderStatus, PaymentStatus,
    menuitem_ingredient_table, Ingredient
)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="supersecret")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------- HOMEPAGE --------------------

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -------------------- LOGIN --------------------

@app.get("/login", response_class=HTMLResponse)
def login_get(request: Request):
    db = SessionLocal()
    waiters = db.query(Staff).filter_by(role=StaffRole.waiter).all()
    kitchen = db.query(Staff).filter_by(role=StaffRole.kitchen).all()
    admins = db.query(Staff).filter_by(role=StaffRole.admin).all()
    db.close()

    return templates.TemplateResponse("login.html", {
        "request": request,
        "waiters": waiters,
        "kitchen": kitchen,
        "admins": admins
    })


@app.post("/login", response_class=HTMLResponse)
def login_post(request: Request, username: str = Form(...), role: str = Form(...)):
    db = SessionLocal()

    # Enum dönüştürme işlemi (örneğin: "waiter" -> StaffRole.waiter)
    try:
        role_enum = StaffRole(role)
    except ValueError:
        db.close()
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid role"
        })

    staff = db.query(Staff).filter_by(name=username, role=role_enum).first()
    db.close()

    if staff:
        request.session["user"] = {
            "id": staff.id,
            "name": staff.name,
            "role": staff.role.value
        }
        return RedirectResponse(f"/{role}/dashboard", status_code=status.HTTP_302_FOUND)
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid credentials"
        })


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=302)


# -------------------- CUSTOMER --------------------

@app.get("/customer", response_class=HTMLResponse)
def customer_get(request: Request):
    db = SessionLocal()
    menu = db.query(MenuItem).all()
    db.close()
    return templates.TemplateResponse("customer_order.html", {"request": request, "menu": menu})


@app.post("/customer", response_class=HTMLResponse)
async def customer_post(request: Request):
    form = await request.form()
    db = SessionLocal()
    menu = db.query(MenuItem).all()

    try:
        table_number = int(form.get("table_number"))
    except (ValueError, TypeError):
        db.close()
        return templates.TemplateResponse("customer_order.html", {
            "request": request,
            "menu": menu,
            "error": "Invalid table number."
        })

    table = db.query(TableModel).filter_by(number=table_number).first()
    if not table:
        db.close()
        return templates.TemplateResponse("customer_order.html", {
            "request": request,
            "menu": menu,
            "error": "Table not found."
        })

    selected_items = []
    for item in menu:
        qty_str = form.get(f"quantity_{item.id}")
        try:
            qty = int(qty_str)
            if qty > 0:
                selected_items.append((item.id, qty))
        except:
            continue

    if not selected_items:
        db.close()
        return templates.TemplateResponse("customer_order.html", {
            "request": request,
            "menu": menu,
            "error": "You must select at least one menu item."
        })

    # -------------------------
    # ✅ STOCK CHECK & DEDUCT
    # -------------------------
    for item_id, qty in selected_items:
        recipe = db.execute(menuitem_ingredient_table.select().where(
            menuitem_ingredient_table.c.menu_item_id == item_id
        )).fetchall()

        for row in recipe:
            ingredient = db.query(Ingredient).get(row.ingredient_id)
            total_needed = row.amount_needed * qty
            if ingredient.stock_quantity < total_needed:
                db.close()
                return templates.TemplateResponse("customer_order.html", {
                    "request": request,
                    "menu": menu,
                    "error": f"❌ Not enough {ingredient.name} in stock to fulfill this order."
                })

    # Deduct now since everything is available
    for item_id, qty in selected_items:
        recipe = db.execute(menuitem_ingredient_table.select().where(
            menuitem_ingredient_table.c.menu_item_id == item_id
        )).fetchall()

        for row in recipe:
            ingredient = db.query(Ingredient).get(row.ingredient_id)
            ingredient.stock_quantity -= row.amount_needed * qty

    # -------------------------
    # ✅ ORDER CREATION - En düşük workload'lu waiter seç
    # -------------------------
    waiter = db.query(Staff).filter_by(role=StaffRole.waiter).order_by(Staff.workload).first()
    if not waiter:
        db.close()
        return templates.TemplateResponse("customer_order.html", {
            "request": request,
            "menu": menu,
            "error": "No waiter available."
        })

    waiter_name = waiter.name
    order = Order(table_id=table.id, waiter_id=waiter.id, status=OrderStatus.pending)
    db.add(order)
    db.flush()

    for item_id, qty in selected_items:
        db.add(OrderItem(order_id=order.id, menu_item_id=item_id, quantity=qty))

    # ✅ DÜZELTİLDİ: Waiter workload'u burada artırılıyor (sipariş atandığında)
    waiter.workload += 1
    db.commit()

    # Get updated menu to reflect current stock
    menu_after = db.query(MenuItem).all()
    db.close()

    return templates.TemplateResponse("customer_order.html", {
        "request": request,
        "menu": menu_after,
        "message": f"✅ Order placed successfully! Assigned to waiter: {waiter_name}"
    })


# -------------------- WAITER --------------------

@app.get("/waiter/dashboard", response_class=HTMLResponse)
def waiter_dashboard(request: Request):
    user = request.session.get("user")
    if not user or user["role"] != "waiter":
        return RedirectResponse("/login")

    db = SessionLocal()
    waiter_id = user["id"]
    pending_orders = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.menu_item),
        joinedload(Order.table)
    ).filter_by(waiter_id=waiter_id, status=OrderStatus.pending).all()

    ready_orders = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.menu_item),
        joinedload(Order.table)
    ).filter_by(waiter_id=waiter_id, status=OrderStatus.ready).all()
    db.close()

    return templates.TemplateResponse("waiter_dashboard.html", {
        "request": request,
        "user": user,
        "pending": pending_orders,
        "ready": ready_orders
    })


@app.post("/waiter/confirm")
def confirm_order(request: Request, order_id: int = Form(...)):
    user = request.session.get("user")
    if not user or user["role"] != "waiter":
        return RedirectResponse("/login")

    db = SessionLocal()
    order = db.query(Order).filter_by(id=order_id, waiter_id=user["id"], status=OrderStatus.pending).first()
    kitchen = db.query(Staff).filter_by(role=StaffRole.kitchen).order_by(Staff.workload).first()

    if order and kitchen:
        order.status = OrderStatus.confirmed
        order.kitchen_id = kitchen.id
        
        # ✅ DÜZELTİLDİ: Kitchen workload'u artırılıyor (sipariş mutfağa atandığında)
        kitchen.workload += 1
        
        # ✅ DÜZELTİLDİ: Waiter workload'u burada artırılmaz (zaten sipariş atanırken artırılmıştı)
        # waiter.workload += 1  <-- Bu satır kaldırıldı
        
        db.commit()

    db.close()
    return RedirectResponse("/waiter/dashboard", status_code=302)


@app.post("/waiter/serve")
def serve_order(request: Request, order_id: int = Form(...), payment_method: str = Form(...)):
    user = request.session.get("user")
    if not user or user["role"] != "waiter":
        return RedirectResponse("/login")

    db = SessionLocal()
    order = db.query(Order).filter_by(
        id=order_id,
        waiter_id=user["id"],
        status=OrderStatus.ready
    ).first()

    if order:
        # Just update order status and payment
        order.status = OrderStatus.served
        order.payment_status = PaymentStatus.paid

        # ✅ DÜZELTİLDİ: Waiter workload'u azaltılıyor (sipariş tamamlandığında)
        waiter = db.query(Staff).filter_by(id=user["id"]).first()
        if waiter and waiter.workload > 0:
            waiter.workload -= 1

        db.commit()

    db.close()
    return RedirectResponse("/waiter/dashboard", status_code=302)


# -------------------- KITCHEN --------------------

@app.get("/kitchen/dashboard", response_class=HTMLResponse)
def kitchen_dashboard(request: Request):
    user = request.session.get("user")
    if not user or user["role"] != "kitchen":
        return RedirectResponse("/login")

    db = SessionLocal()
    staff_id = user["id"]
    orders = db.query(Order).options(
        joinedload(Order.table),
        joinedload(Order.items).joinedload(OrderItem.menu_item)
    ).filter_by(kitchen_id=staff_id, status=OrderStatus.confirmed).all()
    db.close()

    return templates.TemplateResponse("kitchen_dashboard.html", {
        "request": request,
        "user": user,
        "orders": orders
    })


@app.post("/kitchen/prepare")
def kitchen_prepare(request: Request, order_id: int = Form(...)):
    user = request.session.get("user")
    if not user or user["role"] != "kitchen":
        return RedirectResponse("/login")

    db = SessionLocal()
    order = db.query(Order).filter_by(id=order_id, kitchen_id=user["id"], status=OrderStatus.confirmed).first()

    if order:
        order.status = OrderStatus.ready
        
        # ✅ DÜZELTİLDİ: Kitchen workload'u azaltılıyor (sipariş hazır olduğunda)
        staff = db.query(Staff).filter_by(id=user["id"]).first()
        if staff and staff.workload > 0:
            staff.workload -= 1
            
        db.commit()

    db.close()
    return RedirectResponse("/kitchen/dashboard", status_code=302)


# -------------------- ADMIN --------------------

@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    user = request.session.get("user")
    if not user or user["role"] != "admin":
        return RedirectResponse("/login")

    db = SessionLocal()
    ingredients = db.query(Ingredient).all()
    menu = db.query(MenuItem).all()
    db.close()

    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "user": user,
        "ingredients": ingredients,
        "menu": menu
    })


@app.post("/admin/update_stock")
def update_stock(request: Request, ingredient_id: int = Form(...), new_stock: float = Form(...)):
    db = SessionLocal()
    ing = db.query(Ingredient).get(ingredient_id)
    if ing:
        ing.stock_quantity = new_stock
        db.commit()
    db.close()
    return RedirectResponse("/admin/dashboard", status_code=302)


@app.post("/admin/add_ingredient")
def add_ingredient(request: Request, name: str = Form(...), quantity: float = Form(...)):
    db = SessionLocal()
    ing = Ingredient(name=name, stock_quantity=quantity)
    db.add(ing)
    db.commit()
    db.close()
    return RedirectResponse("/admin/dashboard", status_code=302)


@app.post("/admin/add_menu_item")
def add_menu_item(request: Request, name: str = Form(...), price: float = Form(...), recipe: str = Form(...)):
    db = SessionLocal()
    item = MenuItem(name=name, price=price)
    db.add(item)
    db.flush()  # ID gelsin

    try:
        for pair in recipe.split(","):
            ing_id_str, amount_str = pair.split(":")
            ing_id = int(ing_id_str.strip())
            amount = float(amount_str.strip())
            db.execute(menuitem_ingredient_table.insert().values(
                menu_item_id=item.id,
                ingredient_id=ing_id,
                amount_needed=amount
            ))
        db.commit()
    except Exception as e:
        db.rollback()
        print("❌ Invalid recipe:", e)

    db.close()
    return RedirectResponse("/admin/dashboard", status_code=302)


@app.post("/admin/update_price")
def update_price(request: Request, item_id: int = Form(...), new_price: float = Form(...)):
    db = SessionLocal()
    item = db.query(MenuItem).get(item_id)
    if item:
        item.price = new_price
        db.commit()
    db.close()
    return RedirectResponse("/admin/dashboard", status_code=302)


@app.on_event("startup")
def create_initial_tables():
    db = SessionLocal()
    existing = db.query(TableModel).count()
    if existing < 10:
        for i in range(1, 11):
            if not db.query(TableModel).filter_by(number=i).first():
                db.add(TableModel(number=i))
        db.commit()
    db.close()


@app.on_event("startup")
def create_initial_data():
    db = SessionLocal()

    # Masalar
    for i in range(1, 11):
        if not db.query(TableModel).filter_by(number=i).first():
            db.add(TableModel(number=i))

    # Admin varsa ekleme
    if not db.query(Staff).filter_by(name="admin", role="admin").first():
        db.add(Staff(name="admin", role=StaffRole.admin, workload=0))

    db.commit()
    db.close()


@app.on_event("startup")
def create_initial_menu_and_recipes():
    db = SessionLocal()

    # INGREDIENTS
    ingredient_data = [
        ("Bun", 100),
        ("Beef Patty", 100),
        ("Cheese", 100),
        ("Pizza Dough", 100),
        ("Tomato Sauce", 100),
        ("Mozzarella", 100),
        ("Lettuce", 100),
        ("Chicken", 100),
        ("Fries", 100)
    ]

    ingredients = {}
    for name, qty in ingredient_data:
        ing = db.query(Ingredient).filter_by(name=name).first()
        if not ing:
            ing = Ingredient(name=name, stock_quantity=qty)
            db.add(ing)
            db.flush()
        ingredients[name] = ing

    # MENU ITEMS
    menu_items = {
        "Cheeseburger": [("Bun", 1), ("Beef Patty", 1), ("Cheese", 1)],
        "Pizza": [("Pizza Dough", 1), ("Tomato Sauce", 1), ("Mozzarella", 1)],
        "Chicken Wrap": [("Bun", 1), ("Chicken", 1), ("Lettuce", 1)],
        "French Fries": [("Fries", 1)]
    }

    for item_name, recipe in menu_items.items():
        item = db.query(MenuItem).filter_by(name=item_name).first()
        if not item:
            item = MenuItem(name=item_name, price=100)
            db.add(item)
            db.flush()
        for ing_name, amount in recipe:
            ing = ingredients[ing_name]
            exists = db.execute(menuitem_ingredient_table.select().where(
                (menuitem_ingredient_table.c.menu_item_id == item.id) &
                (menuitem_ingredient_table.c.ingredient_id == ing.id)
            )).first()
            if not exists:
                db.execute(menuitem_ingredient_table.insert().values(
                    menu_item_id=item.id,
                    ingredient_id=ing.id,
                    amount_needed=amount
                ))

    db.commit()
    db.close()


@app.get("/debug/recipes")
def debug_recipes():
    db = SessionLocal()
    result = []
    for item in db.query(MenuItem).all():
        recipes = db.execute(
            menuitem_ingredient_table.select().where(
                menuitem_ingredient_table.c.menu_item_id == item.id
            )
        ).fetchall()

        result.append({
            "menu_item": item.name,
            "recipe": [
                {
                    "ingredient_id": row.ingredient_id,
                    "amount_needed": row.amount_needed
                }
                for row in recipes
            ]
        })
    db.close()
    return result


@app.get("/debug/waiters")
def debug_waiters():
    db = SessionLocal()
    waiters = db.query(Staff).filter_by(role=StaffRole.waiter).all()
    result = [
        {"id": w.id, "name": w.name, "workload": w.workload}
        for w in waiters
    ]
    db.close()
    return result


@app.get("/debug/kitchen")
def debug_kitchen():
    db = SessionLocal()
    kitchen_staff = db.query(Staff).filter_by(role=StaffRole.kitchen).all()
    result = [
        {"id": k.id, "name": k.name, "workload": k.workload}
        for k in kitchen_staff
    ]
    db.close()
    return result


@app.get("/debug/reset_workloads")
def reset_workloads():
    db = SessionLocal()
    for staff in db.query(Staff).all():
        staff.workload = 0
    db.commit()
    db.close()
    return {"msg": "Workloads reset to 0."}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()