from shiny import ui
import pandas as pd
import os


def _normalize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Convert all non-numeric, non-boolean columns to string, preserving NA."""
    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_bool_dtype(dtype) or pd.api.types.is_numeric_dtype(dtype):
            continue
        na_mask = df[col].isna()
        df[col] = df[col].astype(str)
        df[col] = df[col].where(~na_mask, other=pd.NA)
    return df


def load_data(file_info):
    """
    Read uploaded file into a pandas DataFrame.
    Supports CSV, XLSX, and JSON.
    """
    if file_info is None:
        return None

    file_path = file_info[0]["datapath"]
    file_name = file_info[0]["name"].lower()

    try:
        if file_name.endswith(".csv"):
            df = pd.read_csv(file_path)
        elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            df = pd.read_excel(file_path)
        elif file_name.endswith(".json"):
            df = pd.read_json(file_path)
        else:
            return None
        return _normalize_dtypes(df)
    except Exception:
        return None

def load_default_data():
    """
    Load built-in dataset (iris).
    """
    file_path = os.path.join(os.getcwd(), "iris_data.csv")
    try:
        return _normalize_dtypes(pd.read_csv(file_path))
    except Exception:
        return None

def upload_ui():
    """
    UI for the data upload section.
    """
    return ui.layout_columns(
        ui.card(
            ui.card_header("Upload Dataset"),
            ui.p("Upload your own dataset or use a built-in sample dataset to explore the app."),

            ui.input_radio_buttons(
                "data_source",
                "Choose data source",
                {
                    "upload": "Upload Your Own File",
                    "sample": "Use Sample Dataset (Iris)",
                },
                selected="upload",
            ),

            ui.input_file(
                "file_upload",
                "Choose a dataset",
                accept=[".csv", ".xlsx", ".xls", ".json"],
                multiple=False,
                width="100%",
            ),

            ui.br(),
            ui.p("Supported formats: CSV, Excel, JSON"),
            ui.output_text_verbatim("upload_status"),
            full_screen=False,
            style="min-width: 360px;",
        ),

        ui.card(
            ui.card_header("Dataset Preview"),
            ui.p("Preview the first few rows of the currently loaded dataset."),
            ui.output_table("data_preview"),
            full_screen=True,
            style="min-width: 0;",
        ),

        col_widths=[5, 7],
    )