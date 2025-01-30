from sqlalchemy import create_engine, Column, Integer, String, Float, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Bill(Base):
    __tablename__ = 'bills'
    id = Column(Integer, primary_key=True)
    employee_id = Column(String)
    amount = Column(Float)
    date = Column(String)  # 实际项目建议用Date类型
    department = Column(String)  # 后续通过Excel填充

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    employee_id = Column(String)
    department = Column(String)

# 初始化数据库
engine = create_engine('sqlite:///bills.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)