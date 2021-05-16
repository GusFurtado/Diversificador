import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html



def table_row(uid:int):
    return html.Tr([
        html.Td(
            dbc.Checkbox(
                checked = True,
                id = {'type': 'checkbox', 'row': uid}
            )
        ),
        html.Td(
            dbc.Input(
                id = {'type': 'input', 'row': uid},
                debounce = True
            )
        ),
        html.Td(
            id = {'type': 'name', 'row': uid}
        )
    ])



main_content = [
    html.H1('Escolha um ticker:'),
    dbc.Table([
        html.Thead([
            html.Th(th) for th in ['🇧🇷', 'Ticker', 'Nome']
        ]),
        html.Tbody([
            table_row(i) for i in ['teste1', 'teste2', 'teste3']
        ])
    ])
]



layout = dbc.Container(
    children = main_content,
    id = 'container'
)