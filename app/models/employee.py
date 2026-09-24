from sqlalchemy import Column,String,Integer
from app.db.db import Base


class EmployeeModel(Base):
    __tablename__="Employees"

    id = Column(Integer,primary_key = True)
    name = Column(String,nullable= False)
    department = Column(String,nullable= False)
    email = Column(String,nullable= False)