import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from utils import menu_ajuda
 


toast = dbc.Toast(
    id = 'ticker_toast',
    dismissable = True,
    is_open = False
)



logo = html.Div([
    html.Div(
        'Desenvolvido com',
        style = {
            'font-size': 12,
            'font-weight': 'bold',
            'color': 'white'
        }
    ),
    html.Div(
        html.A(
            html.Img(
                src = 'https://raw.githubusercontent.com/GusFurtado/DadosAbertosBrasil/master/assets/logo.png',
                height = 40,
                alt = 'Dados Abertos Brasil'
            ),
            href = 'https://www.gustavofurtado.com/dab.html'
        )
    )
],
    style = {
        'position': 'fixed',
        'right': 10,
        'bottom': 10
    }
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
                    autoFocus = True,
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
                    id = 'ticker_analyse',
                    block = True,
                    disabled = True
                ),
                width = {'size': 8, 'offset': 2}
            )
        )
    )
],
    className = 'shadow'
)



layout = html.Div([
    html.Div([
        dcc.Location(id='location'),
        dcc.Store(data=[], id='ticker_data'),
        toast,
        input_box
    ],
        id = 'ticker_box'
    ),
    logo,
    menu_ajuda()
])