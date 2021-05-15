import dash
from dash.dependencies import Output, Input
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
    Output('main_graph', 'figure'),
    Input('ticker_input', 'value'),
    Input('checkbox', 'checked'),
    prevent_initial_call = True)
def selecionar_ticker(ticker, check):
    return utils.timeline(ticker, check)



if __name__ == '__main__':
    app.run_server(
        host = '0.0.0.0',
        port = 1000
    )