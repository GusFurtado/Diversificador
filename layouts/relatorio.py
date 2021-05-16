import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html



jumbotron = dbc.Jumbotron(
    dbc.Container([
        html.H1(
            'Relatório de Análise',
            className = 'display-3'
        ),
        html.P(
            'Esta página conterá as análises de diversificação de portfólio.',
            className = 'lead',
        )
    ],
        fluid = True,
    ),
    fluid = True,
)



main_content = [
    dcc.Location(id='location'),
    jumbotron
]



layout = dbc.Container(
    children = jumbotron,
    id = 'container'
)