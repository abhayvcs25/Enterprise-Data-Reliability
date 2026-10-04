import pandas as pd


class DataTransformation:

    def remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows from the DataFrame."""
        return df.drop_duplicates()

    def remove_nulls(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows containing null values."""
        return df.dropna()

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform the existing basic data cleaning.

        Current cleaning:
        1. Remove duplicate rows.
        2. Remove rows containing null values.
        """
        data = self.remove_duplicates(df)
        data = self.remove_nulls(data)

        return data