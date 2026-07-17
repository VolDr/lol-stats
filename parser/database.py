import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Integer, Date
from sqlalchemy.ext.declarative import declarative_base

path_to_db = '../data'
if not os.path.exists(path_to_db):
    os.mkdir(path_to_db)
engine = create_engine(os.path.join('sqlite:///', path_to_db, 'statistics_analyzer.sqlite?check_same_thread=false'),
                       echo=False)
base = declarative_base()
# session = sessionmaker(bind=engine)()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)
session = Session()