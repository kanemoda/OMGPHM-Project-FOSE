# 🍽️ Restaurant Management System

A full-featured yet simple restaurant management system built with **FastAPI**, **SQLAlchemy**, **Jinja2**, and pure HTML/CSS.

Supports 4 user roles:
- Customer (no login required)
- Waiter
- Kitchen Staff
- Admin

---

## 🚀 Features

✅ Guest customers can place orders  
✅ Waiters confirm & serve orders  
✅ Kitchen staff prepares confirmed orders  
✅ Admin can manage menu, ingredients, stock  
✅ Real-time stock deduction when order is served  
✅ Simple web-based UI  
✅ Smart staff assignment based on workload  

---

## ⚙️ Setup Instructions

### 🛠 Automatic Setup

Run this in terminal:

```bash
chmod +x setup.sh start.sh
./setup.sh
./start.sh
```

This will:
- Create a Python virtual environment
- Install all required packages
- Launch the FastAPI server on `http://127.0.0.1:8000`

---

## 📂 Project Structure

```
restaurant-system/
├── app/
│   ├── __init__.py
│   ├── db.py
│   └── models.py
├── templates/
│   ├── login.html
│   ├── customer_order.html
│   ├── waiter_dashboard.html
│   ├── kitchen_dashboard.html
│   └── admin_dashboard.html
├── static/
│   └── style.css
├── main.py
├── setup.sh
├── start.sh
└── README.md
```

---

## 🌐 Accessing the System

### 👤 Login (for Waiter / Kitchen / Admin)

Navigate to:
```
http://127.0.0.1:8000/login
```

You'll see sample users auto-generated:
- `Waiter1`, `Waiter2`, ...
- `Kitchen1`, `Kitchen2`, ...
- `admin`

Choose one and log in.

### 🍽️ Customer View

Guests can access:
```
http://127.0.0.1:8000/customer
```

Features:
- Select a table (1–10)
- Choose menu items and quantity
- Submit order without login

---

## 🧪 Testing Flow

1. Go to `/customer` and submit an order
2. Log in as `Waiter1` at `/login` and confirm it
3. Log in as `Kitchen1` and mark it as prepared
4. Return to waiter to mark it as served → 💥 stock is reduced!

---

## 🧠 Smart Logic

- Staff are assigned based on **least workload**
- Ingredient stock is deducted based on menu **recipes**
- If insufficient stock exists, order fails to serve

---

## 🧰 Admin Tools

Admin dashboard (`/login → admin`) lets you:
- Add or update menu items
- Add new ingredients
- Update ingredient stock
- Change prices

---

## 🛠 Tech Stack

- FastAPI
- SQLAlchemy
- Jinja2
- SQLite
- HTML & CSS (no JS frameworks)

---

## 🤝 Contributing

This project is open to PRs and extensions. Ideas to extend:
- Add user registration
- Add payment tracking
- Visual charts for admin
- Dockerize fully

---

## 📜 License

MIT © 2025 Efe Deniz Bağlar

Made with ❤️ for learning and fun.
