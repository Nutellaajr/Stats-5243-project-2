from shiny import App, reactive, render, ui
from modules.data_loader import load_data, upload_ui, load_default_data
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
    norm_ui, norm_server,
    apply_all_fe_rules,
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

.info-section {
    margin-top: 30px;
}

.info-section h2 {
    font-weight: 600;
    margin-bottom: 10px;
}

.card {
    border-radius: 12px;
}
.eda-filter-stack {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 8px;
}

"""

navbar_content = ui.page_navbar(
    ui.nav_panel(
        "Home",
        ui.div(
            {"class": "main-container"},
        
            ui.div(
                {"class": "app-title-box"},
                ui.h1({"class": "app-title"}, "DataLytiq"),
                ui.p(
                    {"class": "app-subtitle"},
                    "A modern data application for transforming raw data into actionable insights."
                ),
            ),

            ui.div(
                {"class": "info-section"},
                ui.h2("About DataLytiq"),
                ui.p(
                    "DataLytiq is an interactive data platform built with Python Shiny. "
                    "It allows users to upload datasets, perform data cleaning, engineer features, "
                    "and conduct exploratory data analysis through a seamless and intuitive interface."
                ),
            ),

            ui.layout_columns(

                ui.card(
                    ui.card_header("📂 Data Upload"),
                    ui.p("Import your own datasets in common formats such as CSV, Excel, and JSON, "
                    "or start immediately with a built-in sample dataset. This makes the app "
                     "easy to use for both real project data and quick demonstrations."),
                ),

                ui.card(
                    ui.card_header("🧹 Data Cleaning"),
                    ui.p("Prepare raw data for analysis by handling missing values, duplicates, "
                    "inconsistencies, outliers, and formatting issues. The cleaning module is "
                    "designed to help users create a more reliable and analysis-ready dataset."),
                ),

                ui.card(
                    ui.card_header("⚙️ Feature Engineering"),
                    ui.p("Create new variables and transform existing ones through mapping, binning, "
                    "encoding, and log transformation. This module helps users improve interpretability "
                    "and generate features that better support analysis."),
                ),

                ui.card(
                    ui.card_header("📊 Exploratory Analysis"),
                    ui.p("Explore the structure of your data through summary tables, descriptive "
                    "statistics, and interactive visual analysis. Users can inspect numerical "
                    "patterns, categorical distributions, and relationships between variables."),
                ),

                col_widths=[3, 3, 3, 3],
            ),

            ui.div(
                {"class": "info-section"},
                ui.h2("How to Use"),
                ui.tags.ol(
                    ui.tags.li("Start by uploading a dataset in the Upload tab."),
                    ui.tags.li("Clean and preprocess your data."),
                    ui.tags.li("Create new features."),
                    ui.tags.li("Explore your data through visualizations."),
                ),
            ),
        )
    ),
   
    ui.nav_panel(
        "Upload",
        ui.div(
            {"class": "main-container"},
            ui.div(
                {"class": "app-title-box"},
                ui.div({"class": "app-title"}, "DataLytiq"),
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
            ui.div(
                {
                    "style": (
                        "display:flex; justify-content:space-between; "
                        "align-items:center; gap:12px;"
                    )
                },
                ui.h2("Feature Engineering", {"class": "section-title", "style": "margin-bottom:0;"}),
                ui.input_action_button(
                    "fe_help_btn",
                    "?",
                    class_="btn btn-sm",
                    style=(
                        "width:38px; height:38px; padding:0; "
                        "border:none; background:transparent; box-shadow:none; "
                        "font-weight:800; font-size:24px; line-height:1; "
                        "color:#374151;"
                    ),
                ),
            ),
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
                ui.accordion_panel(
                    "Log Transformation",
                    norm_ui("norm"),
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
    title="DataLytiq",
)

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style(custom_css),
        ui.tags.script(locate_col_js),
    ),
    navbar_content
)


def server(input, output, session):

    @reactive.effect
    @reactive.event(input.fe_help_btn)
    def _show_fe_help_modal():
        ui.modal_show(
            ui.modal(
                ui.div(
                    ui.h4("Feature Engineering Guide"),
                    ui.p(
                        "This module helps you create new variables from the cleaned dataset. "
                        "Each tool applies transformations interactively, and the preview table "
                        "shows the current feature-engineered result."
                    ),

                    ui.hr(),

                    ui.h5("1. Numerical Field Transformation (Map)"),
                    ui.p("Purpose: Create a new field based on a condition applied to one numeric variable."),
                    ui.tags.ul(
                        ui.tags.li("Choose a numeric field."),
                        ui.tags.li("Choose a comparison operator such as <, >, =, <=, or >=."),
                        ui.tags.li("Compare the field to mean, median, or a custom value."),
                        ui.tags.li("Enter a new field name and the value to assign when the condition is true."),
                        ui.tags.li("Click Add rule to create the transformation."),
                    ),
                    ui.p(
                        "Example: If income > mean, then create a new variable such as high_income = True."
                    ),

                    ui.hr(),

                    ui.h5("2. Binning"),
                    ui.p("Purpose: Convert a numeric variable into grouped categories."),
                    ui.tags.ul(
                        ui.tags.li("Choose a numeric field."),
                        ui.tags.li("Check the displayed minimum and maximum values."),
                        ui.tags.li("Enter cutoffs separated by commas."),
                        ui.tags.li("Enter a new field name for the binned variable."),
                        ui.tags.li("Click Apply Binning to create the grouped feature."),
                    ),
                    ui.p(
                        "Example: Age can be converted into groups such as 13-20, 21-30, and 31-40."
                    ),

                    ui.hr(),

                    ui.h5("3. One-Hot Encoding"),
                    ui.p("Purpose: Convert one categorical variable into multiple indicator columns."),
                    ui.tags.ul(
                        ui.tags.li("Choose a field to encode."),
                        ui.tags.li("Click Apply One-Hot."),
                        ui.tags.li("A new boolean column will be created for each unique category."),
                    ),
                    ui.p(
                        "Example: A variable named color may become color_is_red, color_is_blue, and color_is_green."
                    ),

                    ui.hr(),

                    ui.h5("4. Log Transformation"),
                    ui.p("Purpose: Apply a log2 transformation to a numeric variable."),
                    ui.tags.ul(
                        ui.tags.li("Choose a numeric field."),
                        ui.tags.li("Enter a new field name for the transformed variable."),
                        ui.tags.li("Use the preview histograms to compare the original and transformed distributions."),
                        ui.tags.li("Click Apply Log Transformation to create the new feature."),
                    ),
                    ui.p(
                        "Note: Log transformation only works for positive values. Variables with zero or negative values cannot be transformed directly."
                    ),

                    ui.hr(),

                    ui.h5("How to Use the Module"),
                    ui.tags.ul(
                        ui.tags.li("Start from the cleaned dataset."),
                        ui.tags.li("Apply one or more feature engineering tools."),
                        ui.tags.li("Keep useful rules checked in the Applied Rules list."),
                        ui.tags.li("Use the preview table to inspect the current result."),
                        ui.tags.li("Use Locate buttons to quickly find newly created columns in the preview."),
                    ),

                    ui.hr(),

                    ui.h5("Tips"),
                    ui.tags.ul(
                        ui.tags.li("Use clear, descriptive names for new variables."),
                        ui.tags.li("Create features step by step and check the preview after each change."),
                        ui.tags.li("Binning and log transformation are useful for reshaping numeric distributions."),
                        ui.tags.li("One-hot encoding is useful before modeling categorical variables."),
                    ),
                ),
                title="Feature Engineering Help",
                easy_close=True,
                size="l",
            )
        )
    @reactive.calc
    def dataset():
        source = input.data_source()
        file_info = input.file_upload()

        if source == "sample":
            return load_default_data()

        if source == "upload" and file_info is not None:
            df = load_data(file_info)
            if df is not None:
                return df

        return None

    confirmed_filter_rules: reactive.Value = reactive.Value([])

    @reactive.effect
    @reactive.event(input.add_filter_rule)
    def _on_add_filter_rule():
        col = input.filter_col()
        values_raw = input.filter_values()

        if not col or not values_raw.strip():
            return

        drop_vals = sorted({v.strip() for v in values_raw.split(",") if v.strip()})
        if not drop_vals:
            return

        label = f"Dropped {', '.join(drop_vals)} from {col}"
        rule = {"col": col, "values": set(drop_vals), "label": label}
        confirmed_filter_rules.set(confirmed_filter_rules.get() + [rule])

    @output
    @render.ui
    def filter_rules_list():
        rules = confirmed_filter_rules.get()
        if not rules:
            return ui.div()
        return ui.div(
            {"style": "margin-top: 10px; width: 100%;"},
            ui.tags.label("Active Rules"),
            *[
                ui.div(
                    {"style": "display: flex; align-items: center; gap: 8px; width: 100%; margin-top: 4px;"},
                    ui.input_checkbox(f"filter_rule_{i}", rules[i]["label"], value=True),
                )
                for i in range(len(rules))
            ],
        )

    @reactive.calc
    def cleaned_result():
        df = dataset()
        return apply_cleaning(df, input, filter_rules=confirmed_filter_rules.get())

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
            ui.update_selectize("dtype_cols", choices=[], selected=[])
            ui.update_selectize("log_cols", choices=[], selected=[])
            ui.update_selectize("outlier_cols", choices=[], selected=[])
            ui.update_selectize("filter_col", choices=[], selected=[])
            return

        numeric_cols = get_numeric_columns(df)

        ui.update_selectize("scale_cols", choices=numeric_cols, selected=[])
        ui.update_selectize("encode_cols", choices=df.columns.tolist(), selected=[])
        ui.update_selectize("dtype_cols", choices=df.columns.tolist(), selected=[])
        ui.update_selectize("log_cols", choices=numeric_cols, selected=[])
        ui.update_selectize("outlier_cols", choices=numeric_cols, selected=[])
        ui.update_selectize("filter_col", choices=df.columns.tolist(), selected=[])
        
    map_rules  = map_rule_server("map_rule", data=cleaned_df)
    bin_rules  = binning_server("binning", data=cleaned_df)
    ohe_fields = ohe_server("ohe", data=cleaned_df)
    norm_ops   = norm_server("norm", data=cleaned_df)

    curr_df: reactive.Value = reactive.Value(None)

    @reactive.effect
    def _build_curr_df():
        df = dataset()
        if df is None:
            curr_df.set(None)
            return

        result = apply_cleaning(df, input, filter_rules=confirmed_filter_rules.get())
        if result is None:
            curr_df.set(None)
            return
        df, _ = result

        df = apply_all_fe_rules(df, map_rules(), bin_rules(), ohe_fields(), norm_ops())
        curr_df.set(df)

    eda_server(
        input=input,
        output=output,
        session=session,
        raw_data=dataset,
        cleaned_data=cleaned_df,
        fe_data=curr_df, # TODO: All three df shall not be curr_df only. Just pass in curr_df=curr_df and use curr_df in modules/eda.py.
    )

    @output
    @render.data_frame
    def fe_preview():
        df = curr_df()
        if df is None:
            return None
        return df.head()

    
    @output
    @render.text
    def upload_status():
        df = dataset()
        source = input.data_source()

        if df is None:
            if source == "upload":
                return "No dataset uploaded yet."
            return "Sample dataset could not be loaded."

        if source == "sample":
            return f"Using built-in Iris dataset. Rows: {df.shape[0]}, Columns: {df.shape[1]}"

        return f"Upload successful. Rows: {df.shape[0]}, Columns: {df.shape[1]}"

    @output
    @render.table
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
