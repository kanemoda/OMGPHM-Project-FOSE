import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base

# Veritabanı dosyası
DATABASE_URL = "sqlite:///restaurant.db"

# Engine ve session oluşturma
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

# İlk kurulum fonksiyonu
def init_db():
    if not os.path.exists("restaurant.db"):
        Base.metadata.create_all(bind=engine)
        print("✅ Database and tables created.")
    else:
        print("ℹ️  Database already exists.")
