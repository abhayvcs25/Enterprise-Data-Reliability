from sqlalchemy import Column,Integer,String,Boolean,DateTime,func,ForeignKey,Text,JSON
from sqlalchemy.orm import relationship

from app.db.db import Base

class DataQualityResultModel(Base):
    __tablename__ = "DataQualityResult"

    id = Column(Integer,primary_key=True,index=True)
    pipeline_run_id = Column(Integer,ForeignKey("Pipeline_Runs.id"),nullable=False)
    check_name = Column(String(100),nullable=False)
    passed = Column(Boolean,nullable=False)
    metric = Column(JSON,nullable=True)
    rows_affected = Column(Integer,nullable=False)
    message = Column(Text,nullable=True)
    created_at= Column(DateTime,server_default=func.now(),nullable=False)

    pipeline_run = relationship("PipelineRunModel",
                                back_populates="quality_results")
