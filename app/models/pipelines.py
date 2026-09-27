from sqlalchemy import Column,Integer,String,Enum,func,DateTime
import enum
from app.db.db import Base
from sqlalchemy.orm import relationship

class PipelineStatus(str,enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


pipeline_status_enum = Enum(
    PipelineStatus,
    name="pipelinestatus"
)

class PipelinesModel(Base):
    __tablename__ = "Pipelines"

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String,nullable=False,index=True)
    description = Column(String,nullable=True)
    status = Column(pipeline_status_enum,default=PipelineStatus.PENDING,nullable=False)
    created_at = Column(DateTime,server_default=func.now(),nullable=False)
    updated_at = Column(DateTime,server_default=func.now(),onupdate=func.now(),nullable=False)

    runs = relationship("PipelineRunModel",back_populates="pipeline")