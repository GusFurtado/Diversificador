import dash
from dash.dependencies import Output, Input, State, MATCH
import dash_bootstrap_components as dbc

import flask
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug import run_simple

from layouts import tickers
from layouts import relatorio
import utils



MONTSERRAT = {
    'href': 'https://fonts.googleapis.com/css?family=Montserrat',
    'rel': 'stylesheet'
}



server = flask.Flask(__name__)



tickers_app = dash.Dash(
    __name__,
    server = server,
    url_base_pathname = '/tickers/',
    external_stylesheets = [dbc.themes.BOOTSTRAP, MONTSERRAT]
)

tickers_app.title = 'Diversificador de Carteira'
tickers_app.layout = tickers.layout



relatorio_app = dash.Dash(
    __name__,
    server = server,
    url_base_pathname = '/relatorio/',
    external_stylesheets=[dbc.themes.BOOTSTRAP, MONTSERRAT]
)

relatorio_app.title = 'Diversificador de Carteira'
relatorio_app.layout = relatorio.layout



@server.route('/')
def redirect_menu():
    return flask.redirect('/tickers/')
    
@server.route('/tickers/')
def render_app1():
    return flask.redirect('/PyTickers')

@server.route('/relatorio/')
def render_app2():
    return flask.redirect('/PyRelatorio')



@tickers_app.callback(
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



@tickers_app.callback(
    Output('table_body', 'children'),
    Input('new_ticker_button', 'n_clicks'),
    State('table_body', 'children'),
    prevent_initial_call = True)
def add_new_ticker(click, tbody):
    tbody.append(tickers.table_row(click))
    return tbody



@tickers_app.callback(
    Output('location', 'href'),
    Input('analyse_portfolio_button', 'n_clicks'),
    prevent_initial_call = True)
def go_to_report(_):
    return 'http://localhost:1000/relatorio/'



app = DispatcherMiddleware(server, {
    '/PyTickers': tickers_app.server,
    '/PyRelatorio': relatorio_app.server,
})



if __name__ == '__main__':
    run_simple(
        hostname = '0.0.0.0',
        port = 1000,
        application = app,
        use_reloader = True,
        use_debugger = True
    )