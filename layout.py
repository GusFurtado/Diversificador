import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html



main_content = [
    html.H1('Escolha um ticker:'),
    dbc.Row([
        dbc.Col([
            dbc.Label('🇧🇷'),
            dbc.Checkbox(
                checked=True,
                id = 'checkbox'
            )       
        ],
            width = 'auto'
        ),
        dbc.Col(
            dbc.Input(
                id = 'ticker_input',
                debounce = True
            )
        ),
        dbc.Col(
            dcc.Graph(
                id = 'main_graph'
            ),
            width = 8
        )
    ])
]



layout = dbc.Container(
    children = main_content,
    id = 'container'
)