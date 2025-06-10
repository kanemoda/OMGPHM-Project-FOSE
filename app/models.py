from sqlalchemy import Column, Integer, String, ForeignKey, Float, Enum, Table, Boolean
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()

# Enum'lar
class StaffRole(enum.Enum):
    waiter = "waiter"
    kitchen = "kitchen"
    admin = "admin"

class OrderStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    preparing = "preparing"
    ready = "ready"
    served = "served"

class PaymentStatus(enum.Enum):
    unpaid = "unpaid"
    paid = "paid"

# Many-to-Many ilişki: MenuItem <-> Ingredient
menuitem_ingredient_table = Table(
    'menuitem_ingredient',
    Base.metadata,
    Column('menu_item_id', ForeignKey('menu_items.id'), primary_key=True),
    Column('ingredient_id', ForeignKey('ingredients.id'), primary_key=True),
    Column('amount_needed', Float, nullable=False),
)

# Staff: waiter veya kitchen
class Staff(Base):
    __tablename__ = "staff"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    role = Column(Enum(StaffRole), nullable=False)
    workload = Column(Integer, default=0)

# Table: müşteri masası
class TableModel(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True)
    number = Column(Integer, unique=True, nullable=False)

# Ingredient: malzeme
class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    stock_quantity = Column(Float, default=0.0)

# Menu Item: yemek
class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    price = Column(Float, nullable=False)

    ingredients = relationship(
        "Ingredient",
        secondary=menuitem_ingredient_table,
        backref="menu_items"
    )

# Order: sipariş
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    table_id = Column(Integer, ForeignKey("tables.id"))
    waiter_id = Column(Integer, ForeignKey("staff.id"))
    kitchen_id = Column(Integer, ForeignKey("staff.id"), nullable=True)

    status = Column(Enum(OrderStatus), default=OrderStatus.pending)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.unpaid)

    table = relationship("TableModel")
    waiter = relationship("Staff", foreign_keys=[waiter_id])
    kitchen_staff = relationship("Staff", foreign_keys=[kitchen_id])

# OrderItem: sipariş içinde hangi yemekler var
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"))
    quantity = Column(Integer, default=1)

    order = relationship("Order", backref="items")
    menu_item = relationship("MenuItem")
