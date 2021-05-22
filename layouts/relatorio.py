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



layout = html.Div([
    dcc.Location(id='location'),
    jumbotron,
    dbc.Container(
        id = 'container'
    )
])