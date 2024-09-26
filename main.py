import dash, os, sys, random, base64
from dash import html, dcc, Input, Output, callback, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
from io import BytesIO
from jinja2 import Template
# print current directory, absolute path
print(os.path.abspath(os.curdir))
# Read the markdown file
with open('tutorial.md', 'r') as file:
    tutorial_content = file.read()


# global season_id
season_id = random.randint(0, 999999)

setupBaseDir = os.path.dirname(__file__)
sys.path.insert(0, setupBaseDir)
import importlib
FIRST_PART = importlib.import_module("FIRST_PART")

app = dash.Dash(__name__,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                suppress_callback_exceptions=True,
                assets_folder=os.path.join(setupBaseDir, "src"))

# Setup base directory and paths
global dpath_template, dpath_outfiles, results_path
dpath_template = os.path.join(setupBaseDir, 'excel_template', 'template_blank.xlsx')
dpath_outfiles = os.path.join(setupBaseDir, 'outfiles')
result_filename = f"classification_results_{season_id}.xlsx"
results_path = os.path.join(dpath_outfiles, result_filename)
# Define a new dbc.Tab for the About section with detailed content
about_content = html.Div([
    html.Br(),
    html.P("The model was developed by the Childhood Liver Oncology Group (c-LOG) "+
           "at Institut d’Investigació Germans Trias i Pujol (IGTP)."),
    html.P("The Childhood Liver Oncology Group (c-LOG) is a pioneering group focused on translational "+
           "research of paediatric liver cancer in Spain. Its main goals are to increase the molecular "+
           "knowledge of hepatoblastoma, the main liver cancer in children and an extremely rare disease. "+
           "The group aims to understand why these tumors arise in children and to identify biomarkers and "+
           "therapeutic targets to improve quality of life and survival of patients with primary liver cancer. "+
           "In 2010, the group created the first national collection of biospecimens from patients with liver cancer, "+
           "CLCN, which includes samples from adult patients with hepatocellular carcinoma, cirrhosis, "+
           "and chronic hepatitis. The CLCN collection is pivotal for the research conducted by c-LOG, "+
           "benefiting from its participation in the Pediatric Hepatic International Tumor Trial (PHITT) "+
           "and collaborations with over 100 European hospitals."),
    html.Div([
        html.P("Group Leader: Carolina Armengol, ", style={'display': 'inline'}),
        html.A("carmengol@igtp.cat", href="mailto:carmengol@igtp.cat", style={'display': 'inline'})
    ]),
    html.Br(),
    html.A("More about c-LOG",
           href="https://www.germanstrias.org/es/research/cancer/2/oncologia-hepatica-infantil-c-log",
           target="_blank"),
    html.Hr(),
    html.P("The web service was developed by the Machine Learning for Biomedical Research (ML4BioMedR) unit at "+
           "the Barcelona Supercomputing Center (BSC)."),
    html.P("The Machine Learning for Biomedical Research Unit applies machine learning to biomedical problems, " +
           "generating tools and resources for research and secondary data use. It supports projects in precision " +
           "medicine, genomics, and systems biology, leveraging high-performance computing and collaboration with " +
           "specialized groups at BSC. The Unit offers consultancy and technical advice in machine learning, " +
           "develops its own projects, and participates in initiatives like BSC Bioinfo4Women and the ELIXIR " +
           "Machine Learning Focus Group."),
    html.Div([
        html.P("Group Leader: Davide Cirillo, ", style={'display': 'inline'}),
        html.A("davide.cirillo@bsc.es", href="mailto:davide.cirillo@bsc.es", style={'display': 'inline'})
    ]),
    html.Br(),
    html.A("More about ML4BioMedR",
           href="https://www.bsc.es/discover-bsc/organisation/research-departments/machine-learning-biomedical-research",
           target="_blank")
])


# Layout
app.layout = dbc.Container([
    dbc.Row([  # Banner with title and logos
        dbc.Col(html.Img(src=app.get_asset_url("BSC_logo.png"), height="100px"),
                width=3,
                align="left"),
        dbc.Col(html.H1("Hepatoblastoma Classifier",
                        className="text-center",
                        style={'font-weight': 'bold'}),
                width=6,
                align="center"),
        dbc.Col(html.Img(src=app.get_asset_url("IGTP_logo.jpg"), height="150px"),
                width=3,
                align="right"),
    ], className="mb-4"),  # Adds bottom margin to the banner row
    dbc.Row([
        dbc.Col([  # Left column for uploads and operations
            html.Div([
                dbc.Button("Download Excel Template",
                           id="btn_download",
                           color="primary",
                           className="mb-2"),
                dcc.Download(id="download-excel"),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div(['Drag and Drop or ', html.A('Click to Select Files')]),
                    style={
                        'width': '100%', 'height': '60px', 'lineHeight': '60px',
                        'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                        'textAlign': 'center', 'margin': '10px'
                    },
                    multiple=False,
                    accept='.xlsx'
                ),
                html.Div(id='preview-upload')
            ]),
        ], width=4),
        dbc.Col([  # Right column for tabs and results
            dcc.Store(id='store-classification-results'),  # Stores the classification results invisibly
            dbc.Tabs([
                dbc.Tab(html.Div(id='tab-content-results'), label="Classification Results", tab_id="tab-results"),
                dbc.Tab(dcc.Markdown(tutorial_content), label="Tutorial", tab_id="tab-tutorial"),
                dbc.Tab(about_content, label="About", tab_id="tab-about")
            ], id="tabs", active_tab="tab-results")
        ], width=8)
    ])
], fluid=True, className="mt-3")  # Adds top margin to the whole container

@app.callback(
    Output('download-excel', 'data'),
    Input('btn_download', 'n_clicks'),
    prevent_initial_call=True
)
def download_template(n_clicks):
    if n_clicks is None:
        raise PreventUpdate
    return dcc.send_file(dpath_template)

@app.callback(
    [
        Output('store-classification-results', 'data'),
        Output('preview-upload', 'children')
    ],
    Input('upload-data', 'contents'),
    prevent_initial_call=True
)
def update_output(content):
    if content is None:
        return None, "No file uploaded."
    content_type, content_string = content.split(',')
    decoded = base64.b64decode(content_string.encode('utf-8'))
    df = pd.read_excel(BytesIO(decoded), engine='openpyxl')

    # Save the uploaded Excel file to disk
    outfilename = f"output_{season_id}.xlsx"
    output_path = os.path.join(dpath_outfiles, outfilename)
    df.to_excel(output_path, index=False)

    # Pass the file path to FIRST_PART.process_excel
    classification_df = FIRST_PART.process_excel(output_path)

    # Save the classification results to an Excel file
    classification_df.to_excel(results_path, index=False)

    preview = html.Div([
        html.Br(),
        html.P("Preview of Uploaded Dataset", style={'font-weight': 'bold'}),
        dbc.Table.from_dataframe(df.iloc[:,:4], striped=True, bordered=True, hover=True),
    ])

    return classification_df.to_dict('records'), preview

@app.callback(
    Output('tab-content-results', 'children'),
    Input('tabs', 'active_tab'),
    Input('store-classification-results', 'data'),
    prevent_initial_call=True
)

def render_tab_content(active_tab, data):
    if active_tab != "tab-results" or data is None:
        return None
    return html.Div([
        html.Br(),
        html.P("Some explanations here."),
        html.Br(),
        dbc.Button("Download Results", id="btn_download_results", color="primary", className="mb-2"),
        html.Br(),
        html.Br(),
        html.P("Table with classification results. "
               "Each row corresponds to a tumor sample and each column contains a classification result."),
        html.Br(),
        dbc.Table.from_dataframe(pd.DataFrame(data), striped=True, bordered=True, hover=True),
        html.Br(),
        dcc.Download(id="download-results"),

    ])

# Download results as an excel file
@app.callback(
    Output('download-results', 'data'),
    Input('btn_download_results', 'n_clicks'),
    prevent_initial_call=True
)
def download_results(n_clicks):
    if n_clicks is None:
        raise PreventUpdate

    return dcc.send_file(results_path)

if __name__ == '__main__':
    # app.run_server(host='127.0.0.1', port=8050, debug=True)
    app.run_server(host='0.0.0.0', port=8050, debug=True)