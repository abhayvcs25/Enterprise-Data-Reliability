import pandas as pd

class DataTransformation:
    def remove_duplicates(self,df:pd.DataFrame)->pd.DataFrame:
        return df.drop_duplicates()

    def transform(self,df:pd.DataFrame)-> pd.DataFrame:
        data = self.remove_duplicates(df=df)
        return data
