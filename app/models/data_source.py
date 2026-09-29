from app.db.db import Base
from sqlalchemy import Column,Integer,String,ForeignKey,DateTime,Text,Enum,func,JSON
import enum
from sqlalchemy.orm import relationship


class DataSourceType(str,enum.Enum):
    CSV = "CSV"
    POSTGRESQL = "postgresql"
    REST_API = "rest_api"
    MINIO = "minio"


data_source_type_enum = Enum(
    DataSourceType,
    name="datasourcetype"
)

class DataSourceModel(Base):
    __tablename__ = "DataSource"

    id = Column(Integer,primary_key=True,index=True)
    name = Column(String,nullable=False,index=True)
    description = Column(Text,nullable=True)
    source_type = Column(data_source_type_enum,nullable=False)
    location = Column(String,nullable=False)
    configuration = Column(JSON,nullable=True)
    create_at = Column(DateTime,server_default=func.now(),nullable=False)
    updated_at = Column(DateTime,server_default=func.now(),onupdate=func.now(),nullable=False)
    
    pipeline_connections = relationship(
        "PipelineDataSourceModel",
        back_populates="data_source",
        cascade="all, delete-orphan"
    )