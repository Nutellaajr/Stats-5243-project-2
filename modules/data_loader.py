from shiny import ui
import pandas as pd


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
            return pd.read_csv(file_path)
        elif file_name.endswith(".xlsx") or file_name.endswith(".xls"):
            return pd.read_excel(file_path)
        elif file_name.endswith(".json"):
            return pd.read_json(file_path)
        else:
            return None
    except Exception:
        return None


def upload_ui():
    """
    UI for the data upload section.
    """
    return ui.page_fluid(
        ui.card(
            ui.card_header("Upload Dataset"),
            ui.input_file(
                "file_upload",
                "Choose a dataset",
                accept=[".csv", ".xlsx", ".xls", ".json"],
                multiple=False,
            ),
            ui.p("Supported formats: CSV, Excel, JSON"),
            ui.output_text_verbatim("upload_status"),
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Data Preview"),
                ui.output_data_frame("data_preview"),
                full_screen=True,
            ),
            col_widths=[12],
        ),
    )