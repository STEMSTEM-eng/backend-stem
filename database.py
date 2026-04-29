from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
import os
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL не настроен в переменных окружения!")


engine = create_engine(
    DATABASE_URL,

    poolclass=QueuePool,          
    pool_size=5,                  
    max_overflow=10,              
    pool_pre_ping=True,           
    pool_recycle=600,             
    
    
    connect_args={
        "connect_timeout": 10,    
        "sslmode": "require",     
        "sslrootcert": None,      
        "options": "-c timezone=Asia/Almaty"  
    },
    
    
    echo=False,                   
    future=True                   
)


SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False  
)


Base = declarative_base()


def get_db():
    """
    Генератор для получения сессии БД (FastAPI Depends).
    Автоматически закрывает соединение после использования.
    
    Yields:
        Session: Активная сессия SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"❌ Database error: {type(e).__name__}: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Инициализирует базу данных: создаёт все таблицы, если их нет.
    Вызывайте один раз при старте приложения.
    """
    logger.info("🗄️ Инициализация базы данных...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Таблицы созданы/проверены")
    except Exception as e:
        logger.error(f"❌ Ошибка инициализации БД: {e}")
        raise



@event.listens_for(engine, "connect")
def on_connect(dbapi_conn, record):
    """Вызывается при каждом новом подключении к БД"""
    logger.debug("🔗 Новое соединение с БД установлено")


@event.listens_for(engine, "checkout")
def on_checkout(dbapi_conn, connection_record, connection_proxy):
    """Вызывается при получении соединения из пула"""
    logger.debug("📦 Соединение взято из пула")


@event.listens_for(engine, "checkin")
def on_checkin(dbapi_conn, connection_record):
    """Вызывается при возврате соединения в пул"""
    logger.debug("🔄 Соединение возвращено в пул")