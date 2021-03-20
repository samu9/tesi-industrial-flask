from sqlalchemy.ext.declarative import declarative_base

from industrial.database.db import engine
from industrial.database.models import *


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == '__main__':
    init_db()