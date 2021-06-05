import dash_bootstrap_components as dbc
from dash_bootstrap_components._components.Label import Label
import dash_core_components as dcc
import dash_html_components as html

import app_config as cfg
import utils



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
            id = 'corr_timeline_chart',
            config = utils.GRAPH_CONFIG
        )
    )
],
    id = 'corr_timeline_modal',
    is_open = False,
    size = 'lg'
)



portfolios = html.Div([

    dbc.Row([

        # Coluna 1: Efficiency Frontier
        dbc.Col([
            dbc.Label(
                html.B('Escolha um portfólio')
            ),
            dcc.Graph(
                id = 'efficiency_frontier',
                config = utils.GRAPH_CONFIG
            )
        ],
            style = {'padding': 20},
            width = 12,
            lg = 6
        ),

        # Coluna 2: Donut
        dbc.Col([
            dbc.Label(
                html.B('Retorno Esperado')
            ),
            html.Div(
                id = 'portfolios_returns'
            ),
            dcc.Graph(
                id = 'portfolios_chart',
                config = utils.GRAPH_CONFIG
            )
        ],
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



risk_free = html.Div([

    dbc.Row([

        # Coluna 1: Capital Allocation Line
        dbc.Col([
            dbc.Label(
                html.B('Escolha um portfólio')
            ),
            dcc.Graph(
                id = 'capital_allocation_line',
                config = utils.GRAPH_CONFIG
            )
        ],
            style = {'padding': 20},
            width = 12,
            lg = 6
        ),

        # Coluna 2: Final Table
        dbc.Col([
            dbc.Label(
                html.B('Retorno Esperado')
            ),
            html.Div(
                id = 'risk_free_returns'
            ),
            dbc.Table([
                html.Thead(
                    html.Tr([
                        html.Th('Ticker'),
                        html.Th('Proporção')
                    ])
                ),
                html.Tbody(id='risk_free_table')
            ],
                bordered = True
            )
        ],
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
    dcc.Store(id='monthly_returns'),
    dcc.Store(id='portfolios_data'),
    dcc.Store(id='selected_portfolio'),
    corr_timeline_modal,
    jumbotron,
    dbc.Container([
        html.Div(id='corr_table'),
        html.Hr(),
        portfolios,
        html.Hr(),
        risk_free
    ],
        style = {'padding-bottom': 20}
    )
])