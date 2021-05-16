import dash
from dash.dependencies import Output, Input, State, MATCH
import dash_bootstrap_components as dbc

import layout
import utils



MONTSERRAT = {
    'href': 'https://fonts.googleapis.com/css?family=Montserrat',
    'rel': 'stylesheet'
}



app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, MONTSERRAT]
)

app.title = 'Diversificador de Carteira'
app.layout = layout.layout



@app.callback(
    Output({'type': 'name', 'row': MATCH}, 'children'),
    Input({'type': 'input', 'row': MATCH}, 'value'),
    Input({'type': 'checkbox', 'row': MATCH}, 'checked'),
    prevent_initial_call = True)
def set_name(input, check):
    try:
        t = utils.Ticker(input, check)
        return t.name
    except:
        return 'Ticker não encontrado'



@app.callback(
    Output('table_body', 'children'),
    Input('new_ticker_button', 'n_clicks'),
    State('table_body', 'children'),
    prevent_initial_call = True)
def add_new_ticker(click, tbody):
    tbody.append(layout.table_row(click))
    return tbody
    


if __name__ == '__main__':
    app.run_server(
        host = '0.0.0.0',
        port = 1000,
        debug = False
    )