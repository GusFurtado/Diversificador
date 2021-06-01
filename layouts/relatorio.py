import dash_bootstrap_components as dbc
from dash_bootstrap_components._components.Label import Label
import dash_core_components as dcc
import dash_html_components as html

import app_config as cfg



jumbotron = dbc.Jumbotron(
    dbc.Container([
        html.H1(
            cfg.NAME,
            className = 'display-3',
            style = {'text-align': 'center'}
        )
    ],
        fluid = True,
    ),
    fluid = True,
)



corr_timeline_modal = dbc.Modal([
    dbc.ModalHeader(
        id = 'corr_timeline_title'
    ),
    dbc.ModalBody(
        dcc.Graph(
            id = 'corr_timeline_chart'
        )
    ),
    dbc.ModalFooter()
],
    id = 'corr_timeline_modal',
    is_open = False,
    size = 'lg'
)



portfolios = html.Div([

    dbc.Row([

        # Coluna 1
        dbc.Col([
            dbc.Label(
                html.B('Risco do Portfolio')
            ),
            dcc.Slider(
                min = 0,
                max = 99,
                step = 1,
                marks = {
                    0: 'Seguro',
                    99: 'Arriscado'
                },
                value = 0,
                id = 'portfolios_slider'
            ),

            html.Hr(),

            # Expected Returns
            dbc.Label(
                html.B('Retorno Esperado')
            ),
            html.Div(
                id = 'portfolios_returns'
            ),

            html.Hr(),

            dcc.Graph(
                id = 'portfolios_table'
            )
        ],
            style = {'padding': 20},
            width = 12,
            lg = 6
        ),

        # Coluna 2
        dbc.Col(
            dcc.Graph(
                id = 'portfolios_chart'
            ),
            style = {'padding': 20},
            width = 12,
            lg = 6
        )

    ],
        no_gutters = True
    )
],
    className = 'shadow'
)



layout = html.Div([
    dcc.Location(id='location'),
    dcc.Store(id='dataframe'),
    dcc.Store(id='portfolios_data'),
    corr_timeline_modal,
    jumbotron,
    dbc.Container([
        html.Div(id='corr_table'),
        html.Hr(),
        portfolios
    ],
        style = {'padding-bottom': 20}
    )
])