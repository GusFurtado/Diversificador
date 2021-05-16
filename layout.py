import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html



jumbotron = dbc.Jumbotron(
    dbc.Container([
        html.H1(
            'Diversificador de Portfolio',
            className = 'display-3'
        ),
        html.P(
            'Escolha os tickers da sua carteira e clique em "Analisar carteira".',
            className = 'lead',
        )
    ],
        fluid = True,
    ),
    fluid = True,
)



def table_row(uid:int):

    def _table_data(children):
        return html.Td(
            html.Div(
                children,
                className = 'table_data'
            )
        )

    return html.Tr([
        _table_data(
            dbc.Checkbox(
                checked = True,
                id = {'type': 'checkbox', 'row': uid}
            )
        ),
        _table_data(
            dbc.Input(
                debounce = True,
                id = {'type': 'input', 'row': uid}
            )
        ),
        _table_data(
            dcc.Loading(
                html.Div(
                    id = {'type': 'name', 'row': uid}
                ),
                type = 'dot'
            )
        )
    ])



main_content = [
    jumbotron,
    dbc.Table([
        html.Thead([
            html.Th(th) for th in ['🇧🇷', 'Ticker', 'Nome']
        ]),
        html.Tbody(
            [table_row(0)],
            id = 'table_body'
        )
    ]),
    dbc.Row([
        dbc.Col(
            dbc.Button(
                '(+) Adicionar ticker',
                color = 'primary',
                size = 'sm',
                id = 'new_ticker_button'
            ),
            width = 'auto'
        ),
        dbc.Col(
            dbc.Button(
                '(>) Analisar carteira',
                color = 'success',
                size = 'sm',
                id = 'analyse_portfolio_button'
            ),
            width = 'auto'
        ),
    ],
        justify = 'between',
        style = {'margin-bottom': 20}
    )
]



layout = dbc.Container(
    children = main_content,
    id = 'container'
)