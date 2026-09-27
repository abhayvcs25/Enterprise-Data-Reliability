from pydantic import BaseModel,ConfigDict
from app.models.data_source import DataSourceType
from datetime import datetime

class DataSourceCreate(BaseModel):
    name : str
    description :str | None = None
    source_type : DataSourceType
    location :str
    configuration : dict | None = None


class DataSourceResponse(BaseModel):
    id : int
    name : str
    description : str | None = None
    source_type : DataSourceType 
    location : str
    configuration :dict |None = None
    create_at : datetime
    updated_at : datetime


class DataSourceUpdate(BaseModel):
    name : str | None = None
    description : str | None = None
    location : str | None = None
    configuration :dict |None = None