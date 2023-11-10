from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Member(Base):
    __tablename__ = 'members'
    id = Column(Integer, primary_key=True, autoincrement=True)
    member_number = Column(String(50))
    first_name = Column(String)
    last_name = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    tag_ids = Column(String)
