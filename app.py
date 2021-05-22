from socket import gethostname

import dash
from dash.dependencies import Output, Input, State, ALL, MATCH
import dash_bootstrap_components as dbc

import flask
import plotly.io as pio
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug import run_simple

from layouts import tickers
from layouts import relatorio
import utils



MONTSERRAT = {
    'href': 'https://fonts.googleapis.com/css?family=Montserrat',
    'rel': 'stylesheet'
}



# Configs
PORT = 1000
server = flask.Flask(__name__)
pio.templates.default = 'plotly_white'



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
    State({'type': 'name', 'row': ALL}, 'children'),
    State({'type': 'input', 'row': ALL}, 'value'),
    State({'type': 'checkbox', 'row': ALL}, 'checked'),
    prevent_initial_call = True)
def go_to_report(_, names, tickers, b3):
    hashs = utils.get_url_hash(
        tickers = tickers,
        b3 = b3,
        names = names
    )
    return f'http://{gethostname()}:{PORT}/relatorio/{hashs}'



@relatorio_app.callback(
    Output('container', 'children'),
    Input('location', 'hash'))
def load_relatorio(hashtags):
    return utils.load_report(hashtags)



app = DispatcherMiddleware(server, {
    '/PyTickers': tickers_app.server,
    '/PyRelatorio': relatorio_app.server,
})



if __name__ == '__main__':
    run_simple(
        hostname = '0.0.0.0',
        port = PORT,
        application = app
    )