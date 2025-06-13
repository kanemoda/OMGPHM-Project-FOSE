# 🍽️ Restaurant Management System

Simple restaurant management system with **FastAPI** + **SQLAlchemy**.

**4 User Roles:** Customer (no login) • Waiter • Kitchen Staff • Admin

---

## 🚀 Quick Start

### Linux/Mac
```bash
chmod +x *.sh && ./setup.sh && ./start.sh
```

### Windows
```cmd
setup.bat && start.bat
```

**→ Open:** `http://127.0.0.1:8000`

---

## 🎯 How It Works

### Smart Features:
- **Auto staff assignment** - Assigns least busy waiter/kitchen staff
- **Real-time stock tracking** - Ingredients reduce when orders served
- **Recipe-based deduction** - Each menu item has ingredient requirements
- **Session management** - Secure login system
- **Auto database setup** - Creates tables on first run

### User Workflow:
1. **Customers** place orders at `/customer` (no login)
2. **Waiters** confirm orders at `/login` (Waiter1, Waiter2...)
3. **Kitchen** marks orders as prepared (Kitchen1, Kitchen2...)  
4. **Waiters** serve orders → stock automatically reduces
5. **Admin** manages menu, ingredients, prices

**Test Flow:** Order → Waiter confirms → Kitchen prepares → Waiter serves → Stock reduces

---

## 📁 Files

```
├── main.py                    # FastAPI app
├── app/                       # Database & models
├── templates/                 # HTML pages
├── static/style.css          # Styles
├── setup.sh/.bat             # Install dependencies
├── start.sh/.bat             # Run server
└── start_test.sh/.bat        # Run with test data
```

---

## 🧪 Testing

### Quick Test:
```bash
# Linux/Mac
./start_test.sh

# Windows  
start_test.bat
```

### What it does:
- Creates sample menu (Pizza, Burger, etc.)
- Adds ingredients (Cheese, Tomato, etc.)
- Generates test orders
- Simulates full workflow
- Verifies stock deduction logic

### Manual Testing:
1. Go to `/customer` - place an order
2. Login as `Waiter1` - confirm the order  
3. Login as `Kitchen1` - mark as prepared
4. Back to `Waiter1` - serve order
5. Check admin panel - stock reduced! 🎉

---

## 📦 Dependencies

**Python 3.8+** required

### Auto-installed packages:
- **fastapi** - Modern web framework
- **uvicorn** - ASGI server  
- **sqlalchemy** - Database ORM
- **jinja2** - Template engine
- **python-multipart** - Form handling
- **itsdangerous** - Session security
- **pytest** - Testing framework
- **httpx** - HTTP client for tests

### Built-in:
- **sqlite3** - Database (no install needed)

---

## 🤝 Contributing

### Easy extensions:
- **Payment system** - Add order billing
- **User registration** - Custom waiter/kitchen accounts
- **Real-time updates** - WebSocket notifications
- **Mobile design** - Responsive CSS
- **Analytics** - Sales reports & charts
- **Multi-restaurant** - Support multiple branches
- **Docker** - Containerized deployment

### Development:
```bash
git clone <repo>
cd restaurant-system
./setup.sh
# Make changes
./start_test.sh  # Test your changes
```
