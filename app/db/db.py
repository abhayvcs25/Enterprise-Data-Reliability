import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base,sessionmaker

from app.utils.settings import settings


logger = logging.getLogger(__name__)

Base = declarative_base()

engine = create_engine(url=settings.DB_CONNECTION)

local_session = sessionmaker(bind=engine)


try:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        logger.info("Database connected successfully")
except Exception:
    logger.exception("Database connection check failed")

def get_db():
    session = local_session()
    try:
        yield session
    finally:
        session.close()