from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine("mysql+pymysql://root:industrial@localhost:3306/industrial", convert_unicode=False, pool_recycle=1800)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# db = SQLAlchemy()
def init_db():
    import industrial.database.models
    Base.metadata.create_all(bind=engine)