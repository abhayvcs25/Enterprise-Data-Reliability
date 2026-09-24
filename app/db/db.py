from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base,sessionmaker
from app.utils.settings import settings

Base = declarative_base()

engine = create_engine(url=settings.DB_CONNECTION)

local_session = sessionmaker(bind=engine)


try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        print("✅ Database connected successfully")
except Exception as e:
    print("❌ Database connection failed")
    print(e)

def get_db():
    session = local_session()
    try:
        yield session
    except:
        session.close()