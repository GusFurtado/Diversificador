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
            'Escolha ao menos dois tickers para sua carteira e clique em "Analisar carteira >>".',
            className = 'lead',
        )
    ],
        fluid = True,
    ),
    fluid = True,
)



def ticker_card(uid:str) -> dbc.Col:
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



layout = html.Div([
    dcc.Location(id='location'),
    jumbotron,
    dbc.Container([
        dbc.Row([
            ticker_card(f'ticker{i}') for i in range(1,13)
        ]),
        dbc.Row(
            dbc.Col(
                dbc.Button([
                    html.B('Analisar carteira'),
                    html.I(className = 'fas fa-angle-double-right ml-2')
                ],
                    color = 'success',
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