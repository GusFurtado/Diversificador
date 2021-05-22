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



layout = html.Div([
    dcc.Location(id='location'),
    dcc.Store(id='dataframe'),
    corr_timeline_modal,
    jumbotron,
    dbc.Container(
        id = 'container'
    )
])