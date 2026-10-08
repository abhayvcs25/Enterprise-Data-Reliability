from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.data_source import DataSourceType


class SourceConfiguration(BaseModel):
    delimiter: str = ","
    encoding: str = "utf-8"


class SchemaRule(BaseModel):
    enabled: bool = True
    columns: dict[str, str] = Field(default_factory=dict)


class NullRule(BaseModel):
    enabled: bool = True
    columns: dict[str, bool] = Field(default_factory=dict)


class DuplicateRule(BaseModel):
    enabled: bool = True
    columns: list[str] = Field(default_factory=list)


class RangeValue(BaseModel):
    min: int | float | None = None
    max: int | float | None = None


class RangeRule(BaseModel):
    enabled: bool = True
    columns: dict[str, RangeValue] = Field(default_factory=dict)


class RowCountRule(BaseModel):
    enabled: bool = True
    min: int | None = None
    max: int | None = None


class DataQualityRules(BaseModel):
    schema_rule: SchemaRule | None = None
    null_check: NullRule | None = None
    duplicate_check: DuplicateRule | None = None
    range_check: RangeRule | None = None
    row_count: RowCountRule | None = None


class DataQualityConfiguration(BaseModel):
    enabled: bool = False
    rules: DataQualityRules = Field(default_factory=DataQualityRules)


class DataSourceConfiguration(BaseModel):
    source: SourceConfiguration = Field(default_factory=SourceConfiguration)
    data_quality: DataQualityConfiguration | None = None


class DataSourceCreate(BaseModel):
    name: str
    description: str | None = None
    source_type: DataSourceType
    location: str
    configuration: DataSourceConfiguration | None = None


class DataSourceResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    source_type: DataSourceType
    location: str
    configuration: DataSourceConfiguration | None = None
    create_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataSourceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    location: str | None = None
    configuration: DataSourceConfiguration | None = None