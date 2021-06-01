import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html



jumbotron = dbc.Jumbotron(
    dbc.Container([
        html.H1(
            'Diversificador de Portfólio',
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
    html.Div(
        id = 'portfolios_output'
    ),
    html.Div(
        dcc.Graph(
            id = 'portfolios_chart'
        )
    )
])



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