from sqlalchemy.orm import Session
from app.models.data_source import DataSourceModel
from app.schemas.datasourceDto import DataSourceCreate,DataSourceUpdate


class DataSourceRepo:
    def __init__(self,db:Session):
        self.db = db

    def create_dataSource(self,data:DataSourceCreate):
        new_data= DataSourceModel(
            name = data.name,
            description = data.description,
            source_type = data.source_type,
            location = data.location,
            configuration = data.configuration
        )

        self.db.add(new_data)
        self.db.commit()
        self.db.refresh(new_data)

        return new_data

    def get_all(self):
        return self.db.query(DataSourceModel).all()

    def get_by_id(self,data_s_id:int):
        return self.db.query(DataSourceModel).filter(DataSourceModel.id == data_s_id).first()

    def update(self,data_source:DataSourceModel,data:DataSourceUpdate):
        update_data = data.model_dump(exclude_unset=True)

        for filed,value in update_data.items():
            setattr(data_source,filed,value)

        self.db.commit()
        self.db.refresh(data_source)

        return data_source

    def delete(self,data_source:DataSourceModel):
        self.db.delete(data_source)
        self.db.commit()

        return True