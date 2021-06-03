from typing import Container
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

import app_config as cfg



jumbotron = dbc.Jumbotron(
    dbc.Container([
        html.H1(
            cfg.NAME,
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



def ticker_card(uid:int) -> dbc.Col:
    return dbc.Col(
        dbc.Card([
            dbc.CardHeader([
                html.I(className = 'fas fa-plus-circle mr-2'),
                html.Span('Adicionar Ticker')
            ],
                id = {'type': 'name', 'uid': uid}
            ),
            dbc.CardBody(
                dbc.Row([
                    dbc.Col([
                        html.Span(
                            dbc.Label(html.B('B3')),
                            className = 'mr-1'
                        ),
                        html.Span(
                            dbc.Checkbox(
                                checked = True,
                                id = {'type': 'checkbox', 'uid': uid}
                            )
                        )
                    ],
                        width = 'auto'
                    ),
                    dbc.Col(
                        dbc.Input(
                            placeholder = 'Ticker',
                            id = {'type': 'input', 'uid': uid}
                        )
                    )
                ])
            ),
            dbc.CardFooter(
                dbc.Button([
                    html.I(className = 'fas fa-question-circle mr-2'),
                    html.Span('Validar ticker')
                ],
                    color = 'dark',
                    size = 'sm',
                    block = True,
                    id = {'type': 'button', 'uid': uid}
                )
            )
        ],
            color = 'light'
        ),
        style = {'margin-bottom': 20},
        width = 12,
        sm = 6,
        md = 4,
        lg = 3
    )



main_content = [
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



layout = html.Div([
    dcc.Location(id='location'),
    jumbotron,
    dbc.Container([
        dbc.Row([
            ticker_card(i) for i in range(1,13)
        ]),
        dbc.Row(
            dbc.Col(
                dbc.Button([
                    html.Span('Analisar carteira'),
                    html.I(className = 'fas fa-angle-double-right ml-2')
                ],
                    color = 'success',
                    size = 'sm',
                    id = 'analyse_portfolio_button',
                    block = True
                ),
                width = {'size': 8, 'offset': 2}
            )
        ),
    ],
        id = 'container'
    )
])