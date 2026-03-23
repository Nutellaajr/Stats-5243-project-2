'''
Types of functions:

===== Map Rule=====
[Map] [if [field_menu] [op_menu] [val_menu] [op_val_input]] [then convert to field: [new_field_input] and value: [new_value_input]]
field_menu lists the existing fields
op_menu: ["<", ">", "=", "<=", ">="]
val_menu: ["mean", "median", "custom"]
op_val_input: If val_menu is "mean" or "median" then fill with the number in the input box. This shall be calculated upon selection and remember to drop NA. If val_menu is custom then do a trim and numerical check over user input.
new_field_input: trim user input and ensure it's a new field name
new_value_input: if trimmed result is within ["True", "true", "False", "false"] then treat as boolean, if a number then treat as number, otherwise string

===== One-Hot Encoding =====
[One-Hot] [field_menu]
field_menu lists the existing fields
Upon function calling, it will first convert all data in this field to string anyway (including originally number or boolean fields)
After convertion, get the unique values of this field, and then create columns of `is_{field_name}`
Populate the newly created columns with boolean

===== Binning =====
Example:
[Binning] [age]
Min: [13] Max: [55]
Please input cutoffs, separated by comma: [20,30,40,50]
New field name: [age_category]
If the data is int, it will convert to 13-20, 21-30, etc. If the data is double/float, it will convert to 13.0-20.0, 20.0-30.0, etc.
'''

import json
import re

from shiny import module, ui, reactive, render, req
import pandas as pd


# -------------------- SHARED --------------------

def _checkbox_val(input, key: str, default: bool = True) -> bool:
    try:
        return bool(input[key]())
    except Exception:
        return default


# -------------------- MAP RULE --------------------

# -------------------- UI --------------------

@module.ui
def map_rule_ui():
    return ui.div(
        {"class": "map-rule-card"},

        ui.layout_columns(
            ui.div(
                ui.tags.label("Field", {"class": "input-label"}),
                ui.input_select("field_menu", None, choices=[]),
            ),
            ui.div(
                ui.tags.label("Operator", {"class": "input-label"}),
                ui.input_select("op_menu", None,
                                choices=["<", ">", "=", "<=", ">="]),
            ),
            ui.div(
                ui.tags.label("Compare to", {"class": "input-label"}),
                ui.input_select("val_menu", None,
                                choices=["mean", "median", "custom"]),
            ),
            ui.div(
                ui.tags.label("Value", {"class": "input-label"}),
                ui.input_text("op_val_input", None, placeholder="—"),
            ),
            col_widths=[3, 2, 2, 5]
        ),

        ui.layout_columns(
            ui.div(
                ui.tags.label("New field name", {"class": "input-label"}),
                ui.input_text("new_field_input", None, placeholder="e.g. is_high_income"),
            ),
            ui.div(
                ui.tags.label("Assign value", {"class": "input-label"}),
                ui.input_text("new_value_input", None, placeholder="True / False / 1 / text"),
            ),
            col_widths=[6, 6]
        ),

        ui.output_ui("validation_msg"),

        ui.layout_columns(
            ui.input_action_button("add_map", "Add rule",
                                   class_="btn btn-primary mt-2"),
            col_widths=[6],
        ),

        ui.output_ui("rules_list"),
    )


# -------------------- Helpers --------------------

def _parse_value(raw: str):
    s = raw.strip()
    if s.lower() in ("true",  "false"):
        return s.lower() == "true"
    try:
        f = float(s)
        return int(f) if f == int(f) else f
    except ValueError:
        return s


def _apply_map_rule(df: pd.DataFrame, rule: dict) -> pd.DataFrame:
    field = rule["field"]
    operator = rule["operator"]
    threshold = rule["threshold"]
    new_field = rule["new_field"]
    true_value = rule["true_value"]

    ops = {
        "<":  lambda s: s < threshold,
        ">":  lambda s: s > threshold,
        "=":  lambda s: s == threshold,
        "<=": lambda s: s <= threshold,
        ">=": lambda s: s >= threshold,
    }
    mask = ops[operator](df[field])
    
    if new_field not in df.columns:
        df[new_field] = None
    df.loc[mask, new_field] = true_value
    return df


# -------------------- Server --------------------

@module.server
def map_rule_server(input, output, session, data):
    confirmed_rules: reactive.Value[list] = reactive.Value([])
    error_msg: reactive.Value[str] = reactive.Value("")

    # Populate numeric columns
    @reactive.effect
    def _update_fields():
        df = data()
        if df is None:
            ui.update_select("field_menu", choices=[], selected=None, session=session)
            return

        numeric_cols = df.select_dtypes(include="number").columns.tolist()

        selected_col = numeric_cols[0] if numeric_cols else None

        ui.update_select(
            "field_menu",
            choices=numeric_cols,
            selected=selected_col,
            session=session
        )

    # Compute mean/median when field_menu or val_menu changes
    @reactive.calc
    def computed_stat() -> float | None:
        df = data()
        if df is None:
            return None
        col = input.field_menu()
        method = input.val_menu()
        if df is None:
            return None
        if not col or method == "custom":
            return None
        if col not in df.columns:
            return None

        series = df[col].dropna()
        if method == "mean":
            return float(series.mean())
        return float(series.median())

    # Fill op_val_input with mean/median if available
    @reactive.effect
    def _sync_op_val_input():
        stat = computed_stat()
        if stat is not None:
            ui.update_text("op_val_input",
                           value=f"{stat:.4g}",
                           placeholder="auto-computed",
                           session=session)
        else:
            ui.update_text("op_val_input",
                           value="",
                           placeholder="enter a number",
                           session=session)

    # Validation and rule confirmation
    @reactive.effect
    @reactive.event(input.add_map)
    def _on_add():
        error_msg.set("")

        field    = input.field_menu()
        operator = input.op_menu()
        method   = input.val_menu()
        raw_val  = input.op_val_input().strip()
        new_name = input.new_field_input().strip()
        raw_out  = input.new_value_input().strip()

        if method in ("mean", "median"):
            stat = computed_stat()
            if stat is None:
                error_msg.set("Could not compute stat — check the field.")
                return
            threshold = stat
        else:
            try:
                threshold = float(raw_val)
            except ValueError:
                error_msg.set(f"'{raw_val}' is not a valid number.")
                return

        if not new_name:
            error_msg.set("New field name cannot be empty.")
            return

        if not re.fullmatch(r"[A-Za-z0-9_]+", new_name):
            error_msg.set("New field name may only contain letters, digits, and underscores.")
            return

        if not raw_out:
            error_msg.set("Assign value cannot be empty.")
            return
        true_value = _parse_value(raw_out)

        rule = {
            "field":     field,
            "operator":  operator,
            "threshold": threshold,
            "new_field": new_name,
            "true_value":true_value,
            "label":     f"{field} {operator} {threshold:.4g} → {new_name} = {true_value}",
        }
        confirmed_rules.set(confirmed_rules.get() + [rule])

    @output
    @render.ui
    def validation_msg():
        msg = error_msg.get()
        if not msg:
            return ui.div()
        return ui.div(
            {"style": "color: var(--bs-danger); font-size: 12px; margin-top: 6px;"},
            f"Error: {msg}"
        )

    # Render applied rules
    @output
    @render.ui
    def rules_list():
        rules = confirmed_rules.get()
        if not rules:
            return ui.div()
        return ui.div(
            {"style": "margin-top: 10px; width: 100%;"},
            ui.tags.label("Applied Rules", {"class": "input-label"}),
            *[
                ui.div(
                    {"style": "display: flex; align-items: center; gap: 8px; width: 100%;"},
                    ui.div(
                        {"style": "flex: 1; min-width: 0;"},
                        ui.input_checkbox(f"rule_{i}", rules[i]["label"], value=True),
                    ),
                    ui.tags.button(
                        "Locate",
                        {
                            "data-col": rules[i]["new_field"],
                            "onclick": "locateColumn(this.dataset.col)",
                            "class": "btn btn-sm btn-outline-secondary",
                            "style": "flex-shrink: 0; font-size: 11px; padding: 2px 8px;",
                        },
                    ),
                )
                for i in range(len(rules))
            ],
        )

    # Apply all enabled rules to df
    @reactive.calc
    def result() -> pd.DataFrame:
        df = data()
        req(df is not None)
        df = df.copy()
        for i, rule in enumerate(confirmed_rules.get()):
            if not _checkbox_val(input, f"rule_{i}"):
                continue
            try:
                df = _apply_map_rule(df, rule)
            except Exception as e:
                print(f"Rule '{rule['label']}' failed: {e}")
        return df

    return result


# -------------------- BINNING --------------------

# -------------------- UI --------------------

@module.ui
def binning_ui():
    return ui.div(
        {"class": "binning-card"},
        ui.layout_columns(
            ui.div(
                ui.tags.label("Field", {"class": "input-label"}),
                ui.input_select("field_menu", None, choices=[]),
            ),
            ui.div(
                ui.tags.label("Range", {"class": "input-label"}),
                ui.output_ui("field_range"),
            ),
            col_widths=[6, 6],
        ),
        ui.div(
            ui.tags.label("Cutoffs (comma-separated)", {"class": "input-label"}),
            ui.input_text("cutoff_input", None, placeholder="e.g. 20,30,40,50"),
        ),
        ui.layout_columns(
            ui.div(
                ui.tags.label("New field name", {"class": "input-label"}),
                ui.input_text("binning_field_input", None, placeholder="e.g. age_category"),
            ),
            col_widths=[12],
        ),
        ui.layout_columns(
            ui.input_action_button("add_bin", "Apply Binning",
                                   class_="btn btn-primary mt-2"),
            col_widths=[6],
        ),
        ui.output_ui("bin_validation_msg"),

        ui.output_ui("rules_list"),
    )


# -------------------- Helpers --------------------

def _make_bin_labels(edges: list, is_int: bool) -> list[str]:
    labels = []
    for i in range(len(edges) - 1):
        left  = edges[i]
        right = edges[i + 1]
        if is_int:
            display_left = int(left) if i == 0 else int(left) + 1
            labels.append(f"{display_left}-{int(right)}")
        else:
            labels.append(f"{left}-{right}")
    return labels


def _apply_binning(df: pd.DataFrame, op: dict) -> pd.DataFrame:
    df[op["new_col"]] = pd.cut(
        df[op["field"]],
        bins=op["edges"],
        labels=op["labels"],
        right=True,
        include_lowest=True,
    )
    return df


# -------------------- Server --------------------

@module.server
def binning_server(input, output, session, data):
    confirmed_ops: reactive.Value[list] = reactive.Value([])
    error_msg: reactive.Value[str] = reactive.Value("")

    # Populate numeric columns
    @reactive.effect
    def _update_fields():
        df = data()
        if df is None:
            return
        num_cols = df.select_dtypes(include="number").columns.tolist()
        ui.update_select("field_menu", choices=num_cols, session=session)

    # Show min / max
    @output
    @render.ui
    def field_range():
        df  = data()
        col = input.field_menu()
        if df is None or not col or col not in df.columns:
            return ui.span("—", {"style": "color: gray;"})
        series = df[col].dropna()
        if series.empty:
            return ui.span("No data", {"style": "color: gray;"})
        return ui.span(
            f"Min: {series.min()}  |  Max: {series.max()}",
            {"style": "font-size: 12px; color: gray;"},
        )

    # Validate and record operation
    @reactive.effect
    @reactive.event(input.add_bin)
    def _on_add():
        error_msg.set("")

        df = data()
        col = input.field_menu()
        raw_cut = input.cutoff_input().strip()
        new_col = input.binning_field_input().strip()

        if df is None:
            error_msg.set("No dataset loaded.")
            return
        if not col:
            error_msg.set("Please select a field.")
            return
        if not new_col:
            error_msg.set("New field name cannot be empty.")
            return
        if not re.fullmatch(r"[A-Za-z0-9_]+", new_col):
            error_msg.set("New field name may only contain letters, digits, and underscores.")
            return
        if not raw_cut:
            error_msg.set("Please enter at least one cutoff.")
            return

        try:
            cutoffs = [float(x.strip()) for x in raw_cut.split(",") if x.strip()]
        except ValueError:
            error_msg.set("Cutoffs must be numbers separated by commas.")
            return

        cutoffs = sorted(set(cutoffs))

        series  = df[col].dropna()
        col_min = float(series.min())
        col_max = float(series.max())

        for c in cutoffs:
            if c <= col_min or c >= col_max:
                error_msg.set(
                    f"Cutoff {c} must be strictly between min ({col_min}) and max ({col_max})."
                )
                return

        is_int = pd.api.types.is_integer_dtype(df[col])
        edges  = [col_min] + cutoffs + [col_max]
        labels = _make_bin_labels(edges, is_int)

        confirmed_ops.set(confirmed_ops.get() + [{
            "field":   col,
            "edges":   edges,
            "labels":  labels,
            "new_col": new_col,
            "label":   f"{col} → {new_col} ({', '.join(str(c) for c in cutoffs)})",
        }])

    @output
    @render.ui
    def bin_validation_msg():
        msg = error_msg.get()
        if not msg:
            return ui.div()
        return ui.div(
            {"style": "color: var(--bs-danger); font-size: 12px; margin-top: 6px;"},
            f"Error: {msg}"
        )

    # Render applied rules
    @output
    @render.ui
    def rules_list():
        ops = confirmed_ops.get()
        if not ops:
            return ui.div()
        return ui.div(
            {"style": "margin-top: 10px; width: 100%;"},
            ui.tags.label("Applied Rules", {"class": "input-label"}),
            *[
                ui.div(
                    {"style": "display: flex; align-items: center; gap: 8px; width: 100%;"},
                    ui.div(
                        {"style": "flex: 1; min-width: 0;"},
                        ui.input_checkbox(f"rule_{i}", ops[i]["label"], value=True),
                    ),
                    ui.tags.button(
                        "Locate",
                        {
                            "data-col": ops[i]["new_col"],
                            "onclick": "locateColumn(this.dataset.col)",
                            "class": "btn btn-sm btn-outline-secondary",
                            "style": "flex-shrink: 0; font-size: 11px; padding: 2px 8px;",
                        },
                    ),
                )
                for i in range(len(ops))
            ],
        )

    # Apply all enabled rules to df
    @reactive.calc
    def result() -> pd.DataFrame:
        df = data()
        req(df is not None)
        df = df.copy()
        for i, op in enumerate(confirmed_ops.get()):
            if not _checkbox_val(input, f"rule_{i}"):
                continue
            try:
                df = _apply_binning(df, op)
            except Exception as e:
                print(f"Binning on '{op['field']}' failed: {e}")
        return df

    return result


# -------------------- ONE-HOT ENCODING --------------------

# -------------------- UI --------------------

@module.ui
def ohe_ui():
    return ui.div(
        {"class": "ohe-card"},

        ui.layout_columns(
            ui.div(
                ui.tags.label("Field", {"class": "input-label"}),
                ui.input_select("field_menu", None, choices=[]),
            ),
            col_widths=[12],
        ),
        ui.layout_columns(
            ui.input_action_button("add_ohe", "Apply One-Hot", class_="btn btn-primary mt-2"),
            col_widths=[6],
        ),

        ui.output_ui("ohe_validation_msg"),

        ui.output_ui("rules_list"),
    )


# -------------------- Helpers --------------------

def _apply_ohe(df: pd.DataFrame, field: str) -> pd.DataFrame:
    str_col = df[field].where(df[field].isna(), df[field].astype(str))
    unique_vals = str_col.dropna().unique()

    for val in unique_vals:
        safe_name = re.sub(r"[^\w]+", "_", str(val).strip().lower()).strip("_")
        col_name = f"{field}_is_{safe_name}"
        df[col_name] = str_col == val

    return df


# -------------------- Server --------------------

@module.server
def ohe_server(input, output, session, data):
    confirmed_fields: reactive.Value[list] = reactive.Value([])
    error_msg: reactive.Value[str] = reactive.Value("")

    # Populate ALL columns
    @reactive.effect
    def _update_fields():
        df = data()
        if df is None:
            return
        ui.update_select("field_menu", choices=df.columns.tolist(), session=session)

    # Validate and record operation
    @reactive.effect
    @reactive.event(input.add_ohe)
    def _on_add():
        error_msg.set("")
        field = input.field_menu()
        df    = data()

        if not field:
            error_msg.set("Please select a field.")
            return

        if any(f["field"] == field for f in confirmed_fields.get()):
            error_msg.set(f"'{field}' has already been one-hot encoded.")
            return

        cols = []
        if df is not None and field in df.columns:
            str_col     = df[field].where(df[field].isna(), df[field].astype(str))
            unique_vals = str_col.dropna().unique()
            for val in unique_vals:
                safe = re.sub(r"[^\w]+", "_", str(val).strip().lower()).strip("_")
                cols.append(f"{field}_is_{safe}")

        confirmed_fields.set(confirmed_fields.get() + [{"field": field, "cols": cols}])

    @output
    @render.ui
    def ohe_validation_msg():
        msg = error_msg.get()
        if not msg:
            return ui.div()
        return ui.div(
            {"style": "color: var(--bs-danger); font-size: 12px; margin-top: 6px;"},
            f"Error: {msg}"
        )

    # 4. Render applied fields
    @output
    @render.ui
    def rules_list():
        fields = confirmed_fields.get()
        if not fields:
            return ui.div()
        return ui.div(
            {"style": "margin-top: 10px; width: 100%;"},
            ui.tags.label("Applied Rules", {"class": "input-label"}),
            *[
                ui.div(
                    {"style": "display: flex; align-items: center; gap: 8px; width: 100%;"},
                    ui.div(
                        {"style": "flex: 1; min-width: 0;"},
                        ui.input_checkbox(f"rule_{i}", f"One-hot encode: {fields[i]['field']}", value=True),
                    ),
                    ui.tags.button(
                        "Locate",
                        {
                            "data-cols": json.dumps(fields[i]["cols"]),
                            "onclick": "locateColumns(JSON.parse(this.dataset.cols))",
                            "class": "btn btn-sm btn-outline-secondary",
                            "style": "flex-shrink: 0; font-size: 11px; padding: 2px 8px;",
                        },
                    ),
                )
                for i in range(len(fields))
            ],
        )

    # Apply all enabled fields to df
    @reactive.calc
    def result() -> pd.DataFrame:
        df = data()
        req(df is not None)
        df = df.copy()
        for i, entry in enumerate(confirmed_fields.get()):
            if not _checkbox_val(input, f"rule_{i}"):
                continue
            try:
                df = _apply_ohe(df, entry["field"])
            except Exception as e:
                print(f"OHE on '{entry['field']}' failed: {e}")
        return df

    return result