import base64
import io
import json
import os
import requests
import pandas as pd
from dotenv import load_dotenv
import webbrowser
import threading
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

# ===============================
# LOAD ENV
# ===============================
load_dotenv()

base_url = os.getenv("os2iot_BASE_URL").rstrip("/")
os2iot_api = os.getenv("os2iot_api")

headers = {
    "X-API-KEY": os2iot_api,
    "Content-Type": "application/json"
}

FLOAT_TOLERANCE = 1e-9

# ===============================
# DASH APP
# ===============================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "OS2IoT Editor"

app.layout = dbc.Container([

    html.H1("OS2IoT Editor", className="mt-4"),
    html.Hr(),

    html.H4("Upload CSV: name,id,latitude,longitude,metadata"),

    dcc.Upload(
        id='upload-data',
        children=html.Div(['Træk fil hertil eller ', html.A('vælg en fil')]),
        className="border p-3 text-center mb-3",
        multiple=False
    ),

    html.Div(id="file-info"),

    dbc.Button(
        "Generér ændrings-preview",
        id="submit-button",
        color="primary",
        className="mt-3"
    ),

    html.Hr(),

    dbc.Card([
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.H4(id="preview-header")),
                dbc.Col(
                    dbc.Button(
                        "Vis fuld payload",
                        id="show-payload-button",
                        size="sm",
                        disabled=True
                    ),
                    width="auto"
                )
            ])
        ),
        dbc.CardBody(html.Div(id="change-preview"))
    ], className="shadow-sm"),

    dbc.Button(
        "Accepter ændringer",
        id="apply-button",
        color="success",
        className="mt-4",
        disabled=True,
        size="lg"
    ),

    html.Div(id="final-status"),

    dcc.Store(id="payload-store"),

    # ===============================
    # PAYLOAD MODAL
    # ===============================
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("PUT payload")),
            dbc.ModalBody(html.Pre(id="modal-payload-content",
                                   style={"whiteSpace": "pre-wrap"})),
            dbc.ModalFooter(dbc.Button("Luk", id="close-modal"))
        ],
        id="payload-modal",
        is_open=False,
        size="lg"
    ),

    # ===============================
    # CONFIRM MODAL
    # ===============================
    dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Bekræft ændringer")),
            dbc.ModalBody(html.Div(id="confirm-text")),
            dbc.ModalFooter([
                dbc.Button("Annuller", id="cancel-confirm"),
                dbc.Button("Ja, gennemfør ændringer",
                           id="confirm-apply",
                           color="danger")
            ])
        ],
        id="confirm-modal",
        is_open=False
    )

], fluid=False)


# =========================================
# VIS FILINFO
# =========================================
@app.callback(
    Output("file-info", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True
)
def show_file_info(contents, filename):
    decoded = base64.b64decode(contents.split(',')[1])
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
    return dbc.Alert(f"Fil indlæst: {filename} ({len(df)} rækker)",
                     color="success")


# =========================================
# GENERÉR PREVIEW + PAYLOAD
# =========================================
@app.callback(
    Output("change-preview", "children"),
    Output("apply-button", "disabled"),
    Output("show-payload-button", "disabled"),
    Output("payload-store", "data"),
    Output("preview-header", "children"),
    Input("submit-button", "n_clicks"),
    State("upload-data", "contents"),
    prevent_initial_call=True
)
def generate_preview(n_clicks, contents):

    decoded = base64.b64decode(contents.split(',')[1])
    df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))

    preview_rows = []
    payload = []
    change_count = 0

    for _, row in df.iterrows():

        device_id = int(row["id"])
        new_name = row["name"]
        new_lat = float(row["latitude"])
        new_lon = float(row["longitude"])
        new_metadata_raw = row.get("metadata")

        response = requests.get(f"{base_url}/{device_id}", headers=headers)
        if response.status_code != 200:
            continue

        data = response.json()

        coords = data.get("location", {}).get("coordinates", [0, 0])
        current_lon = float(coords[0])
        current_lat = float(coords[1])
        current_name = data.get("name")
        current_metadata_raw = data.get("metadata")

        # Metadata parsing
        try:
            current_meta_obj = json.loads(current_metadata_raw) if current_metadata_raw else {}
        except:
            current_meta_obj = {}

        try:
            new_meta_obj = json.loads(new_metadata_raw) if pd.notna(new_metadata_raw) else current_meta_obj
        except:
            new_meta_obj = current_meta_obj

        metadata_changed = current_meta_obj != new_meta_obj

        lat_changed = abs(current_lat - new_lat) > FLOAT_TOLERANCE
        lon_changed = abs(current_lon - new_lon) > FLOAT_TOLERANCE

        changed = (
            current_name != new_name or
            lat_changed or
            lon_changed or
            metadata_changed
        )

        if changed:
            change_count += 1

            payload.append({
                "id": data["id"],
                "name": new_name,
                "type": data["type"],
                "applicationId": data["application"]["id"],
                "longitude": new_lon,
                "latitude": new_lat,
                "commentOnLocation": data.get("commentOnLocation"),
                "comment": data.get("comment"),
                "metadata": json.dumps(new_meta_obj) if new_meta_obj else None,
                "deviceModelId": data.get("deviceModel"),
                "lorawanSettings": data.get("lorawanSettings")
            })

        preview_rows.append({
            "ID": device_id,
            "Tidligere navn": current_name,
            "Nyt navn": new_name,
            "Tidligere latitude": current_lat,
            "Ny latitude": new_lat,
            "Tidligere longitude": current_lon,
            "Ny longitude": new_lon,
            "Tidligere metadata": current_metadata_raw,
            "Ny metadata": new_metadata_raw,
            "Status": "Ændres" if changed else "Ingen ændring"
        })

    table = dbc.Table.from_dataframe(pd.DataFrame(preview_rows),
                                     striped=True,
                                     bordered=True)

    header = f"Ændringer overblik (Ændres: {change_count} / {len(preview_rows)})"

    return table, change_count == 0, False, payload, header



# =========================================
# ÅBN PAYLOAD MODAL
# =========================================
@app.callback(
    Output("payload-modal", "is_open"),
    Output("modal-payload-content", "children"),
    Input("show-payload-button", "n_clicks"),
    Input("close-modal", "n_clicks"),
    State("payload-store", "data"),
    State("payload-modal", "is_open"),
)
def toggle_payload(show_clicks, close_clicks, payload, is_open):

    if show_clicks and not is_open:
        return True, json.dumps(payload, indent=4, ensure_ascii=False)

    if close_clicks and is_open:
        return False, ""

    return is_open, ""


# =========================================
# CONFIRM MODAL
# =========================================
@app.callback(
    Output("confirm-modal", "is_open"),
    Output("confirm-text", "children"),
    Input("apply-button", "n_clicks"),
    State("payload-store", "data"),
    prevent_initial_call=True
)
def open_confirm(n_clicks, payload):
    return True, f"Er du sikker på at du vil ændre {len(payload)} enheder?"


@app.callback(
    Output("confirm-modal", "is_open", allow_duplicate=True),
    Input("cancel-confirm", "n_clicks"),
    prevent_initial_call=True
)
def close_confirm(n):
    return False


# =========================================
# EXECUTE PUT
# =========================================
@app.callback(
    Output("final-status", "children"),
    Output("confirm-modal", "is_open", allow_duplicate=True),
    Input("confirm-apply", "n_clicks"),
    State("payload-store", "data"),
    prevent_initial_call=True
)
def apply_changes(n_clicks, payload):

    success = 0
    errors = []

    for device in payload:
        device_id = device["id"]
        response = requests.put(f"{base_url}/{device_id}",
                                headers=headers,
                                json=device)

        if response.status_code in [200, 204]:
            success += 1
        else:
            errors.append(f"{device_id}: {response.status_code}")

    if not errors:
        msg = dbc.Alert(f"✅ {success} enheder opdateret korrekt.",
                        color="success")
    else:
        msg = dbc.Alert(
            [html.Div(f"Opdateret: {success}"),
             html.Div(f"Fejl: {len(errors)}"),
             html.Ul([html.Li(e) for e in errors])],
            color="danger"
        )

    return msg, False


def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050")


if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    app.run(debug=False)

