from sqlalchemy import Column,Integer,ForeignKey
from app.db.db import Base
from sqlalchemy.orm import relationship

class PipelineDataSourceModel(Base):
    __tablename__ = "Pipline_DataSource"

    id = Column(Integer,primary_key=True,index=True)
    pipeline_id = Column(Integer,ForeignKey("Pipelines.id",ondelete="CASCADE"),nullable=False)
    datasource_id = Column(Integer,ForeignKey("DataSource.id",ondelete="CASCADE"),nullable=False)
    execution_order = Column(Integer,nullable=True)
    pipeline = relationship(
        "PipelinesModel",
        back_populates="data_source_connections"
    )

    data_source = relationship(
        "DataSourceModel",
        back_populates="pipeline_connections"
    )
    