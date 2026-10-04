import pandas as pd


class DataValidator:

    def check_missing_values(self, data: pd.DataFrame) -> dict:
        """Return the number of missing values in each column."""
        return data.isnull().sum().to_dict()

    def check_duplicates(self, data: pd.DataFrame) -> int:
        """Return the number of duplicate rows."""
        return int(data.duplicated().sum())

    def check_schema(
        self,
        data: pd.DataFrame,
        expected_schema: dict[str, str]
    ) -> dict:
        """Validate DataFrame columns and data types."""

        actual_schema = self._get_actual_schema(data)

        missing_columns = self._find_missing_columns(
            data,
            expected_schema
        )

        unexpected_columns = self._find_unexpected_columns(
            data,
            expected_schema
        )

        type_mismatches = self._find_type_mismatches(
            actual_schema,
            expected_schema
        )

        valid = (
            not missing_columns
            and not unexpected_columns
            and not type_mismatches
        )

        return {
            "valid": valid,
            "missing_columns": missing_columns,
            "unexpected_columns": unexpected_columns,
            "type_mismatches": type_mismatches
        }

    def _get_actual_schema(self, data: pd.DataFrame) -> dict:
        """Return the actual DataFrame schema."""
        return data.dtypes.astype(str).to_dict()

    def _find_missing_columns(
        self,
        data: pd.DataFrame,
        expected_schema: dict[str, str]
    ) -> list:
        """Find columns required by the schema but absent in the DataFrame."""
        return [
            column
            for column in expected_schema
            if column not in data.columns
        ]

    def _find_unexpected_columns(
        self,
        data: pd.DataFrame,
        expected_schema: dict[str, str]
    ) -> list:
        """Find columns present in the DataFrame but absent from the schema."""
        return [
            column
            for column in data.columns
            if column not in expected_schema
        ]

    def _find_type_mismatches(
        self,
        actual_schema: dict,
        expected_schema: dict[str, str]
    ) -> dict:
        """Find columns whose actual type differs from the expected type."""
        return {
            column: {
                "expected": expected_schema[column],
                "actual": actual_schema[column]
            }
            for column in expected_schema
            if (
                column in actual_schema
                and actual_schema[column] != expected_schema[column]
            )
        }