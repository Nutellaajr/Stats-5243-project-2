from shiny import App, reactive, render, ui
from modules.data_loader import load_data, upload_ui
from modules.cleaning import (
    apply_cleaning,
    cleaning_ui,
    build_missing_summary,
    get_numeric_columns,
    get_categorical_columns,
    cleaning_download_handler,
)

from modules.eda import eda_ui, eda_server

from modules.feature_engineering import (
    map_rule_ui, map_rule_server,
    binning_ui, binning_server,
    ohe_ui, ohe_server,
)

locate_col_js = """
function _getHeaders() {
    const container = document.getElementById('fe_preview');
    const scope = container || document;
    return Array.from(scope.querySelectorAll('th, [role="columnheader"]'));
}
function _highlight(el) {
    el.style.transition = 'background 0.4s';
    el.style.background = '#fef08a';
    setTimeout(() => { el.style.background = ''; }, 1800);
}
function locateColumn(colName) {
    const found = _getHeaders().find(h => h.textContent.trim() === colName);
    if (!found) {
        alert('Column "' + colName + '" not found in preview. Make sure the rule is enabled and the preview has loaded.');
        return;
    }
    found.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    _highlight(found);
}
function locateColumns(colNames) {
    const colSet = new Set(colNames);
    const matches = _getHeaders().filter(h => colSet.has(h.textContent.trim()));
    if (!matches.length) {
        alert('Columns not found in preview. Make sure the rule is enabled and the preview has loaded.');
        return;
    }
    matches[0].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    matches.forEach(_highlight);
}
"""

custom_css = """
body {
    background-color: #f6f8fb;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.navbar {
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
    background-color: white !important;
}

.app-title-box {
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    color: white;
    padding: 28px 32px;
    border-radius: 18px;
    margin-bottom: 24px;
    box-shadow: 0 10px 30px rgba(79, 70, 229, 0.18);
}

.app-title {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 8px;
}

.app-subtitle {
    font-size: 1.05rem;
    opacity: 0.95;
    margin-bottom: 0;
}

.section-title {
    font-size: 1.8rem;
    font-weight: 700;
    color: #111827;
    margin-top: 12px;
    margin-bottom: 14px;
}

.section-text {
    color: #4b5563;
    font-size: 1rem;
    margin-bottom: 20px;
}

.card {
    border-radius: 16px !important;
    border: none !important;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.08) !important;
}

.form-control, .btn, .form-select {
    border-radius: 12px !important;
}

.btn-primary {
    background-color: #4f46e5 !important;
    border-color: #4f46e5 !important;
}

.table {
    background-color: white;
    border-radius: 12px;
    overflow: hidden;
}

.placeholder-box {
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 6px 22px rgba(15, 23, 42, 0.08);
    color: #374151;
}

.main-container {
    max-width: 1200px;
    margin: 0 auto;
    padding-top: 10px;
    padding-bottom: 30px;
}

.map-rule-card .form-check,
.binning-card .form-check,
.ohe-card .form-check {
    display: flex;
    align-items: baseline;
    gap: 6px;
    width: 100%;
}

.map-rule-card .form-check-label,
.binning-card .form-check-label,
.ohe-card .form-check-label {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    min-width: 0;
    flex: 1;
}

.eda-var-group {
    margin-bottom: 18px;
}

.eda-var-checkboxes {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 6px;
}

.eda-var-option .form-check {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 0;
}

.eda-var-option .form-check-input {
    margin: 0 !important;
    flex-shrink: 0;
}

.eda-var-option .form-check-label {
    margin: 0 !important;
    line-height: 1.4;
    word-break: break-word;
}
"""

navbar_content = ui.page_navbar(
    ui.nav_panel(
        "Upload",
        ui.div(
            {"class": "main-container"},
            ui.div(
                {"class": "app-title-box"},
                ui.div({"class": "app-title"}, "Project 2 Data App"),
                ui.p(
                    {"class": "app-subtitle"},
                    "An interactive data application for uploading, exploring, and transforming datasets."
                ),
            ),
            upload_ui(),
        )
    ),
    ui.nav_panel(
        "Cleaning",
        cleaning_ui()
    ),
    ui.nav_panel(
        "Feature Engineering",
        ui.div(
            {"class": "main-container"},
            ui.h2("Feature Engineering", {"class": "section-title"}),
            ui.accordion(
                ui.accordion_panel(
                    "Numerical Field Transformation (Map)",
                    map_rule_ui("map_rule"),
                ),
                ui.accordion_panel(
                    "Binning",
                    binning_ui("binning"),
                ),
                ui.accordion_panel(
                    "One-Hot Encoding",
                    ohe_ui("ohe"),
                ),
                open=True,
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Feature Engineered Data Preview"),
                    ui.output_data_frame("fe_preview"),
                    full_screen=True,
                ),
                col_widths=[12],
            ),
        )
    ),
    ui.nav_panel(
        "EDA",
        eda_ui()
    ),
    title="Project 2 Data App",
)

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style(custom_css),
        ui.tags.script(locate_col_js),
    ),
    navbar_content
)


def server(input, output, session):
    @reactive.calc
    def dataset():
        file_info = input.file_upload()
        return load_data(file_info)

    @reactive.calc
    def cleaned_result():
        df = dataset()
        return apply_cleaning(df, input)

    @reactive.calc
    def cleaned_df():
        result = cleaned_result()
        if result is None:
            return None
        df, _ = result
        return df

    @reactive.effect
    def _update_cleaning_choices():
        df = dataset()

        if df is None:
            ui.update_selectize("scale_cols", choices=[], selected=[])
            ui.update_selectize("encode_cols", choices=[], selected=[])
            ui.update_selectize("log_cols", choices=[], selected=[])
            ui.update_selectize("outlier_cols", choices=[], selected=[])
            return

        numeric_cols = get_numeric_columns(df)
        categorical_cols = get_categorical_columns(df)

        ui.update_selectize("scale_cols", choices=numeric_cols, selected=[])
        ui.update_selectize("encode_cols", choices=categorical_cols, selected=[])
        ui.update_selectize("log_cols", choices=numeric_cols, selected=[])
        ui.update_selectize("outlier_cols", choices=numeric_cols, selected=[])

    map_rule_result = map_rule_server("map_rule", data=cleaned_df)
    binning_result = binning_server("binning", data=map_rule_result)
    ohe_result = ohe_server("ohe", data=binning_result)

    eda_server(
        input=input,
        output=output,
        session=session,
        raw_data=dataset,
        cleaned_data=cleaned_df,
        fe_data=ohe_result,
    )

    @output
    @render.data_frame
    def fe_preview():
        df = ohe_result()
        if df is None:
            return None
        return df.head()

    @output
    @render.text
    def upload_status():
        df = dataset()
        if df is None:
            return "No dataset uploaded yet."
        return f"Upload successful. Rows: {df.shape[0]}, Columns: {df.shape[1]}"

    @output
    @render.data_frame
    def data_preview():
        df = dataset()
        if df is None:
            return None
        return df.head()

    @output
    @render.text
    def cleaning_summary():
        result = cleaned_result()
        if result is None:
            return "No cleaning steps applied."

        _, log = result
        if not log:
            return "No cleaning steps applied."

        return "\n".join(log)

    @output
    @render.data_frame
    def missing_table_original():
        df = dataset()
        if df is None:
            return None
        return build_missing_summary(df)

    @output
    @render.data_frame
    def missing_table_cleaned():
        df = cleaned_df()
        if df is None:
            return None
        return build_missing_summary(df)

    @output
    @render.data_frame
    def cleaned_preview():
        df = cleaned_df()
        if df is None:
            return None
        return df.head()

    @output
    @render.text
    def raw_rows():
        df = dataset()
        if df is None:
            return "-"
        return str(df.shape[0])

    @output
    @render.text
    def clean_rows():
        df = cleaned_df()
        if df is None:
            return "-"
        return str(df.shape[0])

    @output
    @render.text
    def rows_removed():
        raw_df = dataset()
        clean_df = cleaned_df()
        if raw_df is None or clean_df is None:
            return "-"
        return str(raw_df.shape[0] - clean_df.shape[0])

    @output
    @render.text
    def raw_cols():
        df = dataset()
        if df is None:
            return "-"
        return str(df.shape[1])

    @output
    @render.text
    def clean_cols():
        df = cleaned_df()
        if df is None:
            return "-"
        return str(df.shape[1])

    @output
    @render.text
    def raw_missing():
        df = dataset()
        if df is None:
            return "-"
        return str(int(df.isna().sum().sum()))

    @output
    @render.text
    def clean_missing():
        df = cleaned_df()
        if df is None:
            return "-"
        return str(int(df.isna().sum().sum()))

    @output
    @render.text
    def raw_dupes():
        df = dataset()
        if df is None:
            return "-"
        return str(int(df.duplicated().sum()))

    @output
    @render.text
    def clean_dupes():
        df = cleaned_df()
        if df is None:
            return "-"
        return str(int(df.duplicated().sum()))

    @output
    @render.download(filename="cleaned_data.csv")
    def download_cleaned():
        yield cleaning_download_handler(cleaned_df())


app = App(app_ui, server)
