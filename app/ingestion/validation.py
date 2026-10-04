import pandas as pd
from app.quality.quality_result import QualityCheckResult

class DataValidator:

    def check_missing_values(self, data: pd.DataFrame) -> QualityCheckResult:
        """Return the number of missing values in each column."""
        missing= data.isnull().sum().to_dict()

        total_missing = sum(missing.values())

        return QualityCheckResult(
            name= "NULL_check",
            passed= total_missing ==0,
            rows_affected= total_missing,
            metric=missing,
            message=(
                "no null value found"
                if total_missing == 0
                else f"Found {total_missing} null values"
                ),
        )

    def check_duplicates(self, data: pd.DataFrame) -> QualityCheckResult:
        """Return the number of duplicate rows."""
        duplicates =  int(data.duplicated().sum())
        return QualityCheckResult(
            name="duplicate_Check",
            passed= duplicates == 0,
            rows_affected= duplicates,
            metric=duplicates,
            message=(
                "no duplicate values"
                if duplicates == 0
                else f"Found {duplicates} duplicate values"
            )
        )

    def check_schema(
        self,
        data: pd.DataFrame,
        expected_schema: dict[str, str]
    ) -> QualityCheckResult:
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
        schema_issues = { "missing_columns": missing_columns, "unexpected_columns": unexpected_columns, "type_mismatches": type_mismatches, }

        return QualityCheckResult(
            name="schema_check",
            passed=valid,
            rows_affected=None,
            metric=schema_issues,
            message=(
                "Schema validation passed"
                if valid
                else "Schema validation failed"
            )
        )

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