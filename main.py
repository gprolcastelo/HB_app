import dash, os, sys, random, base64
from dash import html, dcc, Input, Output, callback, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd
from io import BytesIO
from jinja2 import Template
from PIL import Image

toggle_image = Image.open(os.path.join(os.path.dirname(__file__), 'assets', 'nano_rnaseq.png'))
template_image = Image.open(os.path.join(os.path.dirname(__file__), 'assets', 'template.png'))
results_image = Image.open(os.path.join(os.path.dirname(__file__), 'assets', 'results_overview.png'))

# global season_id
season_id = random.randint(0, 999999)

setupBaseDir = os.path.dirname(__file__)
sys.path.insert(0, setupBaseDir)
import importlib
FIRST_PART = importlib.import_module("FIRST_PART")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True, assets_folder=os.path.join(setupBaseDir, "src"),title="MRS Classifier")
server = app.server
# Setup base directory and paths
global dpath_template, dpath_outfiles, results_path
dpath_template = os.path.join(setupBaseDir, 'excel_template', 'template_blank.xlsx')
dpath_outfiles = os.path.join(setupBaseDir, 'outfiles')
result_filename = f"classification_results_{season_id}.xlsx"
results_path = os.path.join(dpath_outfiles, result_filename)

# Content for the About section
about_content = html.Div([
    html.Br(),
    html.H2("Additional information"),
    html.Hr(),
    html.Br(),
    html.P("The model was developed by the Childhood Liver Oncology Group (c-LOG) at Institut d’Investigació Germans Trias i Pujol (IGTP)."),
    html.P("The Childhood Liver Oncology Group (c-LOG) is an EU reference group on translational research of paediatric liver cancer. The cLOG main goals are to increase the molecular knowledge of childhood liver cancer and specially, hepatoblastoma, the main liver cancer in children and an extremely rare disease. The c-LOG aims to understand why these tumors arise in children and to identify biomarkers and therapeutic targets to improve quality of life and survival of patients with primary liver cancer. The cLOG offers the possibility to study how specific biomarkers of interest are deregulated in liver cancer samples and whether its alteration impacts on patient outcome."),
    html.Div([
        html.P("Group Leader: Carolina Armengol, ", style={'display': 'inline'}),
        html.A("carmengol@igtp.cat", href="mailto:carmengol@igtp.cat", style={'display': 'inline'})
    ]),
    html.Br(),
    html.A("More about c-LOG",
           href="https://www.germanstrias.org/es/research/cancer/2/oncologia-hepatica-infantil-c-log",
           target="_blank"),
    html.Hr(),
    html.Br(),
    html.P("The web service was developed by the Machine Learning for Biomedical Research (ML4BioMedR) unit at the Barcelona Supercomputing Center (BSC)."),
    html.P("The Machine Learning for Biomedical Research Unit applies machine learning to biomedical problems, generating tools and resources for research and secondary data use. It supports projects in precision medicine, genomics, and systems biology, leveraging high-performance computing and collaboration with specialized groups at BSC. The Unit offers consultancy and technical advice in machine learning, develops its own projects, and participates in initiatives like BSC Bioinfo4Women and the ELIXIR Machine Learning Focus Group."),
    html.Div([
        html.P("Group Leader: Davide Cirillo, ", style={'display': 'inline'}),
        html.A("davide.cirillo@bsc.es", href="mailto:davide.cirillo@bsc.es", style={'display': 'inline'})
    ]),
    html.Br(),
    html.A("More about ML4BioMedR", href="https://www.bsc.es/discover-bsc/organisation/research-departments/machine-learning-biomedical-research", target="_blank"),
    html.Hr(),
])

# Content for the Tutorial section:
tutorial_content = html.Div([
    html.Br(),
    html.H2("Tutorial"),
    html.Br(),
    html.P("Step-by-Step Guide to use the MRS."),
    html.Br(),
    html.H3("1. Download the Template File"),
    html.P("Start by downloading the Excel template provided. Click the \"Download Excel Template\" button at the top left of the screen. This template is pre-structured to simplify entering the required molecular data for each patient."),
    html.Br(),
    html.H3("2.What to include"),
    html.Br(),
    html.P("Transcriptomic data:"),
    html.Ul([
        html.Li([
            "Data from 19 genes obtained via ",
            html.B("Nanostring"),
            " or ",
            html.B("RNA-seq"),
            " (ensure data is normalized beforehand). Required for classifying tumors based on:"
        ]),
        html.Ul([
        html.Li("The 16+VIM-gene signature: (AFP, BUB1, DLG7, DUSP9, E2F5, IGSF1, NLE, RPL10A, ALDH2, APCS, APOC4, AQP9, C1S, CYP2E1, GHR, HPD, and VIM)."),
        html.Li("The 14q32-gene signature: (DLK1 and MEG3)."),
        ]),
        html.Li("Epigenetic data:"),
        html.Ul([
        html.Li([
        "Global DNA methylation values measured via ",
            html.B("QuALU"),
            " (Quantification of Unmethylated Alu; Percentage of Unmethylated Alu [PUMA] values) or ",
            html.B("850k-array"),
            " (Illumina; mean β-values of CpGs)."
        ])
        ]),
    ]),
    html.Blockquote(
        html.P([
            html.I([
                html.B("Important"),
                ": Paired or unpaired non-tumor samples are required for the classification. A minimal number of 5 non-tumor samples is recommended. Please discard any reference sample with any degree of tumor contamination."
            ])
        ]),
        style={'background-color': '#f9f9f9', 'border-left': '10px solid #ccc', 'padding': '10px'}),
    html.H3("3. Fill in the Template"),
    html.P("Using the Excel template, carefully enter the data for each sample. Follow these guidelines:"),
    html.Ul([
        html.Li(["Naming Samples:"]),
        html.Ul([
            html.Li(["Tumor Samples: Use names starting with \"T_\" (e.g., T_01, T_02,...)"]),
            html.Li(["Non-Tumor Samples: Use names starting with \"NT_\" (e.g., NT_01, NT_02,...)"])
            ]),
        html.Li(["Unique Names: Ensure each sample name is unique and not repeated."])
    ]),
    html.P(["Take your time to verify that all data is correctly entered, as accuracy is critical for correct stratification."]),
    html.Br(),
    html.H3("4. Upload the Completed Template"),
    html.P("Select whether your data comes from Nanostring or RNA-seq by clicking the appropriate option (“Nano” or “RNAseq”)."),
    html.Br(),
    # insert image from local file
    html.Img(
        src=toggle_image,
        style={'width': '100%'},
        alt="Nano or RNA-seq toggle",
    ),
    html.Br(),
    html.P("Once the template is filled (see example below), upload the excel file to the server by either dragging and dropping the file into the designated area or by manually selecting the file."),
    html.Br(),
    html.Img(
        src=template_image,
        style={'width': '100%'},
        alt="Results Overview",
    ),
    html.Br(),
    html.Br(),
    html.Br(),
    html.Blockquote(
        html.P([
            html.I([
                html.B("Important"),
                ": A correctly formatted file will upload without errors and output will be revealed. If any issues occur or no result appears on the screen, please check the file for compliance with the template structure."
            ])
        ]),
        style={'background-color': '#f9f9f9', 'border-left': '10px solid #ccc', 'padding': '10px'}),
    html.Br(),
    html.H3("5. View the Results"),
    html.P("After the upload is successful, go to the “Classification Results” tab. Here’s what you’ll find: "),
    html.Ul([
        html.Li(["Stratification Results (Right): A detailed table showing molecular classifications, including risk stratification based on available biomarkers."]),
        html.Li(["Dataset Preview (Left): A summary of the uploaded data for reference"])
    ]),
    html.Img(
        src=results_image,
        style={'width': '100%'},
        alt="Results Overview",
    ),
    html.Br(),
    html.P("If some biomarkers are missing, the tool will provide classifications for the available data but will not calculate the full Molecular Risk Stratification (MRS)."),
    html.Br(),
    html.H3("6. Download the Results"),
    html.P("Save your results for further analysis. Click the \"Download Results\" button (highlighted in blue) to export the results as an Excel file."),
    html.Hr(),
    html.Br(),
    html.Br(),
    html.Br(),
])

# Getting started section content (welcome message)
getting_started_content = html.Div([
    html.Br(),
    html.H2("Getting Started"),
    html.Br(),
    html.P("Welcome to the HB Molecular Risk Stratifier! "),
    html.P("MRS is an online computational tool designed for research purposes that allows the classification of patients with hepatoblastoma (HB) into distinct risk groups based on the tumor and non-tumor liver transcriptomic and epigenetic data as already detailed in Carrillo-Reixach et al (2020) and Del Rio-Álvarez et al. (2025)."),
    html.P("By integrating molecular information obtained from different techniques, MRS-HB provides researchers the possibility to classify patients according tumor molecular fingerprint, contributing to validate the impact on molecular data into patient outcome and in the future, contribute to the development of personalized treatment strategies."),
    html.P("MRS-HB is designed by the Childhood Liver Oncology Group (c-LOG) at Institut d’Investigació Germans Trias i Pujol (IGTP) and the Biomedical Research (ML4BioMedR) unit at the Barcelona Supercomputing Center (BSC)."),
    html.Hr(),
])

# how to cite section content
how_to_cite_content = html.Div([
    html.Br(),
    html.H2("How to cite us?"),
    html.Br(),
    html.P("Please cite the following papers if you use MRS tool in your research:"),
    html.Ul([
        html.Li(["Del Río-Álvarez A, Jimenez-Duran G, Royo L, Lozano J et al. (2025).Validation of prognostic biomarkers of hepatoblastoma using formalin-fixed paraffin-embedded samples from patients of the European SIOPEL-3 clinical trial. "]),
        html.Li(["Carrillo-Reixach J, Torrens L, Simon-Coma M, Royo L, Domingo-Sàbat M, Abril-Fornaguera J, et al. Epigenetic footprint enables molecular risk stratification of hepatoblastoma with clinical implications. J Hepatol. 1;73(2):328–41."]),
        ]),
    html.Hr(),
])

# Warning section content
warning_conent = html.Div([
    html.Br(),
    html.H2("Warnings!"),
    html.Br(),
    html.P("The MRS does not store any of the data once the site is reloaded or disconnected."),
    html.P("This tool is only for research use. Any commercial or clinical use is not authorized."),
    html.Hr(),
])

# Contact section content
contact_content = html.Div([
    html.Br(),
    html.H2("Contact"),
    html.Br(),
    html.P("Thank you for using our tool! Your feedback is valuable for improving our platform. If you have any questions or need support, don't hesitate to contact us through the provided channels."),
    html.Div([
        html.P("If you have any questions, please contact:", style={'display': 'inline'}),
        html.A("carmengol@igtp.cat", href="mailto:carmengol@igtp.cat", style={'display': 'inline'})
    ]),
    html.Hr(),
])

# Layout
app.layout = dbc.Container([
    dbc.Row([  # Banner with title and logos
        dbc.Col(html.Img(src=app.get_asset_url("BSC_logo.png"), height="100px"), width=3, align="center"),
        dbc.Col(html.Img(src=app.get_asset_url("logo_MRS-removebg-preview.png"), height="100px"), width=3, align="center"),
        dbc.Col(html.Img(src=app.get_asset_url("IGTP_logo.jpg"), height="150px"), width=3, align="center"),
    ], className="mb-4", justify="between"),  # Adds bottom margin to the banner row
    dbc.Row([
        dbc.Col([  # Left column for uploads and operations
            html.Div([
                dbc.Button("Download Excel Template", id="btn_download", color="primary", className="mb-2"),
                dcc.RadioItems(
                    id='toggle-analysis',
                    options=[
                        {'label': 'Nano', 'value': 'nano'},
                        {'label': 'RNAseq', 'value': 'rnaseq'}
                    ],
                    value='nano',
                    labelStyle={'display': 'inline-block', 'margin-right': '10px'}
                ),
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
            dcc.Store(id='store-rnaseq-analysis', data=False),  # Store for rnaseq_analysis variable
            dbc.Tabs([
                dbc.Tab(html.Div(id='tab-content-results'), label="Classification Results", tab_id="tab-results"),
                dbc.Tab(tutorial_content, label="Tutorial", tab_id="tab-tutorial"),
                dbc.Tab(how_to_cite_content, label="How to Cite", tab_id="tab-cite"),
                dbc.Tab(warning_conent, label="Warning", tab_id="tab-warning"),
                dbc.Tab(contact_content,label="Contact", tab_id="tab-contact"),
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
    State('store-rnaseq-analysis', 'data'),
    prevent_initial_call=True
)
def update_output(content, rnaseq_analysis):
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
    classification_df = FIRST_PART.process_excel(output_path, rnaseq_analysis)

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
    prevent_initial_call=False
)
def render_tab_content(active_tab, data):
    if active_tab != "tab-results" or data is None:
        return getting_started_content
    return html.Div([
        html.Br(),
        dbc.Button("Download Results", id="btn_download_results", color="primary", className="mb-2"),
        html.Br(),
        html.Br(),
        html.P("Table with classification results. Each row corresponds to a tumor sample and each column contains a classification result."),
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

@app.callback(
    Output('store-rnaseq-analysis', 'data'),
    Input('toggle-analysis', 'value')
)
def set_analysis_type(value):
    return value == 'rnaseq'

if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)