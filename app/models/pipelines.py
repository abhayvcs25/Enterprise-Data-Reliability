from sqlalchemy import Column,Integer,String,Enum,func,DateTime
import enum
from app.db.db import Base

class PipelineStatus(str,enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class PipelinesModel(Base):
    __tablename__ = "Pipelines"

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String,nullable=False,index=True)
    description = Column(String,nullable=True)
    status = Column(Enum(PipelineStatus),default=PipelineStatus.PENDING,nullable=False)
    created_at = Column(DateTime,server_default=func.now(),nullable=False)
    updated_at = Column(DateTime,server_default=func.now(),onupdate=func.now(),nullable=False)
