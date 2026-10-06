from sqlalchemy import (
    Column,
    Integer,
    Enum,
    func,
    DateTime,
    ForeignKey,
    Float,
    Text
)
from sqlalchemy.orm import relationship

from app.db.db import Base
from app.models.pipelines import PipelineStatus


class PipelineRunModel(Base):
    __tablename__ = "Pipeline_Runs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    pipeline_id = Column(
        Integer,
        ForeignKey("Pipelines.id"),
        nullable=False
    )

    status = Column(
        Enum(PipelineStatus),
        nullable=False
    )

    started_at = Column(
        DateTime,
        server_default=func.now(),
        nullable=False
    )

    finished_at = Column(
        DateTime,
        nullable=True
    )

    duration = Column(
        Float,
        nullable=True
    )

    error_message = Column(
        Text,
        nullable=True
    )

    pipeline = relationship(
        "PipelinesModel",
        back_populates="runs"
    )

    quality_results = relationship(
        "DataQualityResultModel",
        back_populates="pipeline_run",
        cascade="all, delete-orphan"
    )