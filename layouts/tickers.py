import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html



toast = dbc.Toast(
    id = 'ticker_toast',
    dismissable = True,
    is_open = False
)



input_box = dbc.Card([
    dbc.CardHeader([
        html.I(className='fas fa-tags mr-2'),
        html.Span('Monte sua carteira')
    ]),
    dbc.CardBody([
        dbc.Row([
            dbc.Col([
                html.Span(
                    dbc.Label(html.B('B3')),
                    className = 'mr-1'
                ),
                html.Span(
                    dbc.Checkbox(
                        checked = True,
                        id = 'ticker_checkbox'
                    )
                )
            ],
                width = 'auto'
            ),
            dbc.Col(
                dbc.Input(
                    placeholder = 'Adicione um ticker',
                    id = 'ticker_input'
                )
            ),
            dbc.Col(
                dbc.Button(
                    html.I(className='fas fa-plus-circle'),
                    color = 'success',
                    id = 'ticker_add'
                ),
                width = 'auto'
            )
        ]),
        html.Hr(),
        dbc.Row(
            id = 'ticker_tags',
            justify = 'around'
        )
    ]),
    dbc.CardFooter(
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
        )
    )
],
    className = 'shadow'
)



layout = html.Div([
    dcc.Location(id='location'),
    dcc.Store(data=[], id='ticker_data'),
    toast,
    input_box
],
    id = 'ticker_box'
)