import io
import re
from typing import Iterable

import numpy as np
import pandas as pd
from shiny import ui
from sklearn.preprocessing import MinMaxScaler, StandardScaler


def _make_unique(names: list[str]) -> list[str]:
    """Ensure column names stay unique after cleaning."""
    seen: dict[str, int] = {}
    result: list[str] = []

    for name in names:
        if name not in seen:
            seen[name] = 1
            result.append(name)
        else:
            seen[name] += 1
            result.append(f"{name}_{seen[name]}")

    return result


def _standardize_single_name(name: str) -> str:
    """Convert one column name to a clean snake_case style."""
    name = str(name).strip().lower()
    name = re.sub(r"[-\s]+", "_", name)
    name = re.sub(r"[^\w]", "", name)
    return name


def _standardize_column_names(columns: Iterable) -> list[str]:
    """Standardize a list of column names and keep them unique."""
    cleaned = [_standardize_single_name(col) for col in columns]
    return _make_unique(cleaned)


def _build_column_mapping(original_cols: list[str], cleaned_cols: list[str]) -> dict[str, str]:
    """Map original column names to standardized names."""
    return {str(old): str(new) for old, new in zip(original_cols, cleaned_cols)}


def _map_selected_columns(selected_cols, col_map: dict[str, str], current_cols: list[str]) -> list[str]:
    """Map UI-selected columns to the dataframe's current column names."""
    if not selected_cols:
        return []

    mapped = []
    current_set = set(current_cols)

    for col in selected_cols:
        col = str(col)

        if col in current_set:
            mapped.append(col)
            continue

        mapped_col = col_map.get(col)
        if mapped_col in current_set:
            mapped.append(mapped_col)

    seen = set()
    unique_mapped = []
    for col in mapped:
        if col not in seen:
            seen.add(col)
            unique_mapped.append(col)

    return unique_mapped


def _trim_string_values(df: pd.DataFrame) -> pd.DataFrame:
    """Trim leading and trailing whitespace in text columns."""
    out = df.copy()

    for col in out.select_dtypes(include=["object", "string"]).columns:
        out[col] = out[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    return out


def _missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Create a column-level summary of missing values."""
    if df is None:
        return pd.DataFrame(columns=["column", "missing_count", "missing_pct", "dtype"])

    if df.empty:
        return pd.DataFrame(
            {
                "column": df.columns,
                "missing_count": [0] * len(df.columns),
                "missing_pct": [0.0] * len(df.columns),
                "dtype": [str(dtype) for dtype in df.dtypes],
            }
        )

    counts = df.isna().sum()
    pct = (counts / len(df) * 100).round(2)

    summary = pd.DataFrame(
        {
            "column": counts.index,
            "missing_count": counts.values,
            "missing_pct": pct.values,
            "dtype": df.dtypes.astype(str).values,
        }
    )

    return summary.sort_values(
        by=["missing_count", "column"],
        ascending=[False, True]
    ).reset_index(drop=True)


def _get_categorical_columns(df: pd.DataFrame) -> list[str]:
    """Return columns suitable for one-hot encoding."""
    if df is None:
        return []

    return df.select_dtypes(include=["object", "string", "category"]).columns.tolist()


def _get_numeric_columns(df: pd.DataFrame) -> list[str]:
    """Return numeric columns."""
    if df is None:
        return []

    return df.select_dtypes(include=np.number).columns.tolist()


def cleaning_ui():
    """Build the UI for the data cleaning and preprocessing section."""
    return ui.page_fluid(
        ui.layout_columns(
            ui.card(
                ui.card_header("Cleaning Controls"),
                ui.p(
                    "Select the preprocessing steps to apply. "
                    "The cleaned output updates automatically after each change."
                ),
                ui.accordion(
                    ui.accordion_panel(
                        "1 · Standardization",
                        ui.tags.small(
                            "Standardize column names and remove extra whitespace so downstream analysis is easier to manage."
                        ),
                        ui.input_checkbox(
                            "standardize_names",
                            "Standardize column names (snake_case)",
                            value=True,
                        ),
                        ui.input_checkbox(
                            "trim_strings",
                            "Trim whitespace in text columns",
                            value=True,
                        ),
                    ),
                    ui.accordion_panel(
                        "2 · Duplicates",
                        ui.tags.small(
                            "Detect and remove duplicate rows before further preprocessing."
                        ),
                        ui.input_checkbox(
                            "remove_duplicates",
                            "Remove duplicate rows",
                            value=False,
                        ),
                    ),
                    ui.accordion_panel(
                        "3 · Missing Values",
                        ui.tags.small(
                            "Choose whether to remove missing data or impute it with summary statistics."
                        ),
                        ui.input_select(
                            "missing_strategy",
                            "Strategy",
                            {
                                "none": "Do nothing",
                                "drop_rows": "Drop rows by missing-value percentage",
                                "drop_cols": "Drop columns by missing-value percentage",
                                "mean_mode": "Impute numeric with mean, categorical with mode",
                                "median_mode": "Impute numeric with median, categorical with mode",
                            },
                            selected="none",
                        ),
                        ui.input_slider(
                            "missing_threshold",
                            "Drop only if missing % exceeds",
                            min=0,
                            max=100,
                            value=0,
                            step=5,
                            post="%",
                        ),
                        ui.p(
                            ui.tags.small(
                                "For drop strategies, a threshold of 0% means any missing value triggers removal."
                            )
                        ),
                    ),
                    ui.accordion_panel(
                        "4 · Scaling",
                        ui.tags.small(
                            "Scale numeric variables when features are on very different ranges."
                        ),
                        ui.input_select(
                            "scaling_method",
                            "Method",
                            {
                                "none": "None",
                                "standard": "Standard scaling (z-score)",
                                "minmax": "Min-max scaling [0, 1]",
                            },
                            selected="none",
                        ),
                        ui.input_selectize(
                            "scale_cols",
                            "Numeric columns to scale",
                            choices=[],
                            multiple=True,
                        ),
                    ),
                    ui.accordion_panel(
                        "5 · Encoding",
                        ui.tags.small(
                            "Convert categorical variables into numeric indicators for downstream modeling."
                        ),
                        ui.input_checkbox(
                            "encode_categorical",
                            "One-hot encode categorical columns",
                            value=False,
                        ),
                        ui.input_selectize(
                            "encode_cols",
                            "Columns to encode (leave blank = all categorical)",
                            choices=[],
                            multiple=True,
                        ),
                    ),
                    ui.accordion_panel(
                        "6 · Data Type Conversion",
                        ui.tags.small(
                            "Convert selected columns to a target type. This is useful when numeric codes actually represent categories."
                        ),
                        ui.input_checkbox(
                            "convert_dtype",
                            "Convert data type",
                            value=False,
                        ),
                        ui.input_selectize(
                            "dtype_cols",
                            "Columns to convert",
                            choices=[],
                            multiple=True,
                        ),
                        ui.input_select(
                            "dtype_target",
                            "Target type",
                            {
                                "category": "Category",
                                "string": "String",
                                "integer": "Integer",
                                "float": "Float",
                            },
                            selected="category",
                        ),
                    ),
                    ui.accordion_panel(
                        "7 · Transformations",
                        ui.tags.small(
                            "Optional transformations can help reduce skewness. Log transform is applied only to strictly positive numeric columns."
                        ),
                        ui.input_checkbox(
                            "apply_log_transform",
                            "Apply log transform",
                            value=False,
                        ),
                        ui.input_selectize(
                            "log_cols",
                            "Columns to transform (leave blank = none)",
                            choices=[],
                            multiple=True,
                        ),
                    ),
                    ui.accordion_panel(
                        "8 · Outliers",
                        ui.tags.small(
                            "Use the IQR rule to either cap extreme values or remove rows containing outliers."
                        ),
                        ui.input_checkbox(
                            "handle_outliers",
                            "Handle outliers with the IQR rule",
                            value=False,
                        ),
                        ui.input_selectize(
                            "outlier_cols",
                            "Numeric columns to check (leave blank = all numeric)",
                            choices=[],
                            multiple=True,
                        ),
                        ui.input_select(
                            "outlier_action",
                            "Strategy",
                            {
                                "cap": "Cap outliers to the IQR fences",
                                "remove": "Remove rows containing outliers",
                            },
                            selected="cap",
                        ),
                        ui.input_numeric(
                            "iqr_multiplier",
                            "IQR multiplier",
                            value=1.5,
                            min=0.5,
                            max=5.0,
                            step=0.1,
                        ),
                    ),
                    ui.accordion_panel(
                        "9 · Value Filtering",
                        ui.tags.small(
                            "Drop rows where a specific column contains one or more exact values. Add multiple rules; uncheck any to disable it."
                        ),
                        ui.input_selectize(
                            "filter_col",
                            "Column to filter on",
                            choices=[],
                            multiple=False,
                        ),
                        ui.input_text(
                            "filter_values",
                            "Values to drop (comma-separated)",
                            placeholder="e.g. Exempt, Unknown",
                        ),
                        ui.input_action_button(
                            "add_filter_rule",
                            "Add Rule",
                            class_="btn btn-primary btn-sm mt-2",
                        ),
                        ui.output_ui("filter_rules_list"),
                    ),
                    open=False,
                ),
                ui.hr(),
                ui.download_button("download_cleaned", "Download Cleaned CSV"),
                full_screen=False,
            ),
            ui.card(
                ui.card_header("Before vs After Overview"),
                ui.layout_columns(
                    ui.value_box("Original rows", ui.output_text("raw_rows")),
                    ui.value_box("Cleaned rows", ui.output_text("clean_rows")),
                    ui.value_box("Rows removed", ui.output_text("rows_removed")),
                    ui.value_box("Original columns", ui.output_text("raw_cols")),
                    ui.value_box("Cleaned columns", ui.output_text("clean_cols")),
                    ui.value_box("Original missing", ui.output_text("raw_missing")),
                    ui.value_box("Cleaned missing", ui.output_text("clean_missing")),
                    ui.value_box("Original duplicates", ui.output_text("raw_dupes")),
                    ui.value_box("Cleaned duplicates", ui.output_text("clean_dupes")),
                    col_widths=[4, 4, 4, 4, 4, 4, 4, 4, 4],
                ),
                full_screen=False,
            ),
            col_widths=[4, 8],
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Applied Operations Log"),
                ui.output_text_verbatim("cleaning_summary"),
                full_screen=True,
            ),
            ui.card(
                ui.card_header("Missing Value Summary"),
                ui.layout_columns(
                    ui.card(
                        ui.card_header("Original"),
                        ui.output_data_frame("missing_table_original"),
                    ),
                    ui.card(
                        ui.card_header("After Cleaning"),
                        ui.output_data_frame("missing_table_cleaned"),
                    ),
                    col_widths=[6, 6],
                ),
                full_screen=True,
            ),
            col_widths=[4, 8],
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Cleaned Data Preview"),
                ui.output_data_frame("cleaned_preview"),
                full_screen=True,
            ),
            col_widths=[12],
        ),
    )


def apply_cleaning(df: pd.DataFrame, input, filter_rules=None) -> tuple[pd.DataFrame | None, list[str]]:
    """
    Apply user-selected cleaning and preprocessing steps.

    Returns a cleaned dataset together with a step-by-step log
    describing what was applied or skipped.
    """
    if df is None:
        return None, ["No dataset loaded."]

    cleaned = df.copy()
    log: list[str] = []

    original_cols = [str(col) for col in cleaned.columns]
    col_map = {col: col for col in original_cols}

    if input.standardize_names():
        new_cols = _standardize_column_names(original_cols)
        col_map = _build_column_mapping(original_cols, new_cols)
        cleaned.columns = new_cols

        renamed_count = sum(old != new for old, new in zip(original_cols, new_cols))
        if renamed_count > 0:
            log.append(f"Standardized column names ({renamed_count} column(s) renamed).")
        else:
            log.append("Column names were already clean.")
    else:
        log.append("Column-name standardization skipped.")

    if input.trim_strings():
        cleaned = _trim_string_values(cleaned)
        log.append("Trimmed leading and trailing whitespace in text columns.")
    else:
        log.append("Whitespace trimming skipped.")

    if input.remove_duplicates():
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates()
        removed = before - len(cleaned)
        log.append(f"Removed {removed} duplicate row(s).")
    else:
        log.append("Duplicate removal skipped.")

    strategy = input.missing_strategy()
    threshold = float(input.missing_threshold()) / 100.0

    if strategy == "drop_rows":
        row_missing_pct = cleaned.isna().mean(axis=1)
        before = len(cleaned)
        cleaned = cleaned.loc[row_missing_pct <= threshold].copy()
        removed = before - len(cleaned)
        log.append(
            f"Dropped {removed} row(s) with missing-value percentage above {input.missing_threshold()}%."
        )

    elif strategy == "drop_cols":
        col_missing_pct = cleaned.isna().mean(axis=0)
        before_cols = cleaned.shape[1]
        cleaned = cleaned.loc[:, col_missing_pct <= threshold].copy()
        removed = before_cols - cleaned.shape[1]
        col_map = {k: v for k, v in col_map.items() if v in cleaned.columns}

        log.append(
            f"Dropped {removed} column(s) with missing-value percentage above {input.missing_threshold()}%."
        )

    elif strategy in {"mean_mode", "median_mode"}:
        numeric_cols = _get_numeric_columns(cleaned)
        categorical_cols = _get_categorical_columns(cleaned)

        imputed_num = 0
        imputed_cat = 0
        use_mean = strategy == "mean_mode"

        for col in numeric_cols:
            if cleaned[col].isna().any():
                fill_value = cleaned[col].mean() if use_mean else cleaned[col].median()
                cleaned[col] = cleaned[col].fillna(fill_value)
                imputed_num += 1

        for col in categorical_cols:
            if cleaned[col].isna().any():
                mode_vals = cleaned[col].mode(dropna=True)
                if not mode_vals.empty:
                    cleaned[col] = cleaned[col].fillna(mode_vals.iloc[0])
                    imputed_cat += 1

        method_label = "mean" if use_mean else "median"
        log.append(
            f"Imputed {imputed_num} numeric column(s) with {method_label} and "
            f"{imputed_cat} categorical column(s) with mode."
        )

    else:
        log.append("Missing values left unchanged.")

    if input.convert_dtype():
        selected_dtype_cols = _map_selected_columns(
            input.dtype_cols(),
            col_map,
            cleaned.columns.tolist(),
        )
        target_type = input.dtype_target()

        converted_cols = []
        skipped_cols = []

        for col in selected_dtype_cols:
            try:
                if target_type == "category":
                    cleaned[col] = cleaned[col].astype("category")
                elif target_type == "string":
                    cleaned[col] = cleaned[col].astype("string")
                elif target_type == "integer":
                    cleaned[col] = pd.to_numeric(cleaned[col], errors="raise").astype("Int64")
                elif target_type == "float":
                    cleaned[col] = pd.to_numeric(cleaned[col], errors="raise").astype(float)

                converted_cols.append(col)
            except Exception:
                skipped_cols.append(col)

        if converted_cols:
            log.append(
                f"Converted {len(converted_cols)} column(s) to {target_type}: {', '.join(converted_cols)}."
            )
        elif input.dtype_cols():
            log.append("Data type conversion skipped because the selected columns could not be converted.")
        else:
            log.append("Data type conversion selected, but no columns were chosen.")

        if skipped_cols:
            log.append(f"Skipped data type conversion for: {', '.join(skipped_cols)}.")
    else:
        log.append("Data type conversion skipped.")

    scaling_method = input.scaling_method()
    selected_scale_cols = _map_selected_columns(
        input.scale_cols(),
        col_map,
        cleaned.columns.tolist(),
    )

    if scaling_method != "none" and selected_scale_cols:
        valid_cols = [
            col for col in selected_scale_cols
            if pd.api.types.is_numeric_dtype(cleaned[col])
        ]

        if valid_cols:
            scaler = StandardScaler() if scaling_method == "standard" else MinMaxScaler()
            cleaned[valid_cols] = scaler.fit_transform(cleaned[valid_cols])

            scale_label = (
                "standard scaling (z-score)"
                if scaling_method == "standard"
                else "min-max scaling"
            )
            log.append(f"Applied {scale_label} to: {', '.join(valid_cols)}.")
        else:
            log.append("Scaling skipped because no valid numeric columns were selected.")
    elif scaling_method == "none":
        log.append("Scaling skipped.")
    else:
        log.append("Scaling method selected, but no columns were chosen.")

    if input.encode_categorical():
        selected_encode_cols = _map_selected_columns(
            input.encode_cols(),
            col_map,
            cleaned.columns.tolist(),
        )

        if selected_encode_cols:
            categorical_now = set(_get_categorical_columns(cleaned))
            cat_cols = [col for col in selected_encode_cols if col in categorical_now]
        else:
            cat_cols = _get_categorical_columns(cleaned)

        if cat_cols:
            cleaned = pd.get_dummies(cleaned, columns=cat_cols, drop_first=False, dtype=int)
            log.append(
                f"One-hot encoded {len(cat_cols)} categorical column(s): {', '.join(cat_cols)}."
            )
        else:
            log.append("Encoding skipped because no eligible categorical columns were found.")
    else:
        log.append("Categorical encoding skipped.")

    if input.apply_log_transform():
        selected_log_cols = _map_selected_columns(
            input.log_cols(),
            col_map,
            cleaned.columns.tolist(),
        )

        if selected_log_cols:
            valid_log_cols = [
                col for col in selected_log_cols
                if pd.api.types.is_numeric_dtype(cleaned[col])
            ]
        else:
            valid_log_cols = []

        transformed_cols = []
        skipped_cols = []

        for col in valid_log_cols:
            series = cleaned[col]
            if series.notna().all() and (series > 0).all():
                cleaned[col] = np.log(series)
                transformed_cols.append(col)
            else:
                skipped_cols.append(col)

        if transformed_cols:
            log.append(f"Applied log transform to: {', '.join(transformed_cols)}.")
        elif input.log_cols():
            log.append("Log transform skipped because selected columns were not valid strictly positive numeric variables.")
        else:
            log.append("Log transform selected, but no columns were chosen.")

        if skipped_cols:
            log.append(
                f"Skipped log transform for non-positive or missing-value columns: {', '.join(skipped_cols)}."
            )
    else:
        log.append("Log transform skipped.")

    if input.handle_outliers():
        multiplier = float(input.iqr_multiplier())
        selected_outlier_cols = _map_selected_columns(
            input.outlier_cols(),
            col_map,
            cleaned.columns.tolist(),
        )

        numeric_candidates = _get_numeric_columns(cleaned)
        target_cols = selected_outlier_cols if selected_outlier_cols else numeric_candidates
        target_cols = [col for col in target_cols if col in numeric_candidates]

        if not target_cols:
            log.append("Outlier handling skipped because no numeric columns were available.")
        else:
            action = input.outlier_action()

            if action == "remove":
                mask = pd.Series(True, index=cleaned.index)

                for col in target_cols:
                    q1 = cleaned[col].quantile(0.25)
                    q3 = cleaned[col].quantile(0.75)
                    iqr = q3 - q1

                    if pd.isna(iqr) or iqr == 0:
                        continue

                    lower = q1 - multiplier * iqr
                    upper = q3 + multiplier * iqr
                    mask &= cleaned[col].between(lower, upper, inclusive="both")

                before = len(cleaned)
                cleaned = cleaned.loc[mask].copy()
                removed = before - len(cleaned)
                log.append(
                    f"Removed {removed} row(s) containing IQR-based outliers in: {', '.join(target_cols)}."
                )

            else:
                capped_cols = 0

                for col in target_cols:
                    q1 = cleaned[col].quantile(0.25)
                    q3 = cleaned[col].quantile(0.75)
                    iqr = q3 - q1

                    if pd.isna(iqr) or iqr == 0:
                        continue

                    lower = q1 - multiplier * iqr
                    upper = q3 + multiplier * iqr
                    cleaned[col] = cleaned[col].clip(lower=lower, upper=upper)
                    capped_cols += 1

                log.append(
                    f"Capped outliers using the IQR rule on {capped_cols} column(s): {', '.join(target_cols)}."
                )
    else:
        log.append("Outlier handling skipped.")

    active_filter_rules = filter_rules or []

    for i, rule in enumerate(active_filter_rules):
        try:
            enabled = bool(input[f"filter_rule_{i}"]())
        except Exception:
            enabled = True

        if not enabled:
            continue

        col = rule["col"]
        drop_vals = rule["values"]

        if col in cleaned.columns:
            before = len(cleaned)
            cleaned = cleaned[~cleaned[col].astype(str).isin(drop_vals)].copy()
            removed = before - len(cleaned)
            log.append(
                f"Dropped {removed} row(s) where '{col}' was in: {', '.join(sorted(drop_vals))}."
            )

    if not active_filter_rules:
        log.append("Value filtering skipped.")

    log.append(
        f"Final dataset shape: {cleaned.shape[0]:,} row(s) × {cleaned.shape[1]:,} column(s)."
    )

    return cleaned, log


def build_missing_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Return a column-level missing-value summary table."""
    return _missing_summary(df)


def cleaning_download_handler(cleaned_df: pd.DataFrame):
    """Convert the cleaned dataframe to downloadable CSV bytes."""
    if cleaned_df is None:
        return b""

    buffer = io.StringIO()
    cleaned_df.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def get_numeric_columns(df: pd.DataFrame) -> list[str]:
    """Return numeric columns for UI selection controls."""
    return _get_numeric_columns(df)


def get_categorical_columns(df: pd.DataFrame) -> list[str]:
    """Return categorical columns for UI selection controls."""
    return _get_categorical_columns(df)

def get_categorical_columns(df: pd.DataFrame) -> list[str]:
    """Return categorical columns for UI selection controls."""
    return _get_categorical_columns(df)
    
