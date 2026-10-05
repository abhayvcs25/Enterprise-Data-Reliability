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

    def check_range(self,
                    data:pd.DataFrame,
                    column:str,
                    min_value:int=None,
                    max_value:int = None,
                    min_inclusive:bool=True,
                    max_inclusive:bool=True)->QualityCheckResult:
        if column not in data.columns:
            return QualityCheckResult(
                name="Range_check",
                passed=False,
                rows_affected=0,
                metric={
                    "column":column,
                    "rule":"column does not exist"
                },
                message=f"'{column}' does not exits"
            )

        if not pd.api.types.is_numeric_dtype(data[column]):
            return QualityCheckResult(
                name="Range_check",
                passed=False,
                rows_affected=0,
                metric={
                    "column":column,
                    "rule":"numeric column required"
                },
                message=f"'{column}' must be numeric dtype for validation"
            )

        if min_value is None and max_value is None:
            return QualityCheckResult(
                name="Range_check",
                passed=False,
                rows_affected=0,
                metric={
                    "column":column,
                    "rule":"min and max required"
                },
                message="At least one of min_value or max_value must be provided"
            )

        value = data[column]

        invalid_mask=pd.Series(False,index=data.index)
        rules_part=[]
        if min_inclusive is not None:
            if min_inclusive:
                invalid_mask |=value < min_value
                rules_part.append(f"{column}>{min_value}")
            else:
                invalid_mask |= value <= min_value
                rules_part.append(f"{column}>={min_value}")

        if max_inclusive is not None:
            if max_inclusive:
                invalid_mask |=value > max_value
                rules_part.append(f"{column}<{max_value}")
            else:
                invalid_mask |= value<= min_value
                rules_part.append(f"{column}<={max_value}")

        affected_rows= int(invalid_mask.sum())
        rule = " and ".join(rules_part)

        return QualityCheckResult(
            name="range_check",
            passed=affected_rows == 0,
            rows_affected=affected_rows,
            metric={
                "column": column,
                "rule": rule,
                "violations": affected_rows,
            },
            message=(
                f"All values in '{column}' satisfy the rule: {rule}"
                if affected_rows == 0
                else f"Found {affected_rows} rows violating the rule: {rule}"
            ),
        )

    def count_rows(self,data:pd.DataFrame,
                   min_rows:int=None,
                   max_rows:int=None)->QualityCheckResult:
        total_rows= len(data)

        if min_rows is None or max_rows is None:
            return QualityCheckResult(
                name="Rows_check",
                passed=False,
                rows_affected=0,
                metric={
                    "message":"min and max rows validation Failed"
                },
                message="min/max rows can't be None"
            )

        if min_rows>total_rows or total_rows>max_rows:
            return QualityCheckResult(
                name="Rows_check",
                passed=False,
                rows_affected=0,
                metric={
                    "message":"min and max rows validation Failed"
                },
                message="length of the data is < || > the min/max value"
            )

        return QualityCheckResult(
            name="Rows_check",
            passed=True,
            rows_affected=0,
            metric={
                "message":"min and max rows validation Passed"
            },
            message="length of the data is with in the range of min/max value"
        )