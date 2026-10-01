import pandas as pd


class DataValidator:
    def check_missing_values(self, data: pd.DataFrame) -> dict:
        return data.isnull().sum().to_dict()

    def check_duplicates(self, data: pd.DataFrame) -> int:
        return int(data.duplicated().sum())

    def check_schema(
        self,
        data: pd.DataFrame,
        expected_schema: dict[str, str]
    ) -> dict:

        actual_schema = data.dtypes.astype(str).to_dict()

        missing_columns = [
            column
            for column in expected_schema
            if column not in data.columns
        ]

        unexpected_columns = [
            column
            for column in data.columns
            if column not in expected_schema
        ]

        type_mismatches = {
            column: {
                "expected": expected_schema[column],
                "actual": actual_schema[column]
            }
            for column in expected_schema
            if column in actual_schema
            and actual_schema[column] != expected_schema[column]
        }

        valid = (
            len(missing_columns) == 0
            and len(unexpected_columns) == 0
            and len(type_mismatches) == 0
        )

        return {
            "valid": valid,
            "missing_columns": missing_columns,
            "unexpected_columns": unexpected_columns,
            "type_mismatches": type_mismatches
        }