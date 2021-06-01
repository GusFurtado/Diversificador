from socket import gethostname

import dash
from dash.dependencies import Output, Input, State, ALL, MATCH
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

import flask
import plotly.io as pio
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug import run_simple

from layouts import tickers
from layouts import relatorio
import utils



MONTSERRAT = {
    'href': 'https://fonts.googleapis.com/css2?family=Montserrat:wght@300;800&display=swap',
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
def set_name(ticker, b3):
    return utils.get_name(ticker, b3)



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
    Output('corr_table', 'children'),
    Output('dataframe', 'data'),
    Output('portfolios_data', 'data'),
    Input('location', 'hash'))
def load_relatorio(hashtags):
    report = utils.Markowitz(hashtags)
    return (
        report.corr_table(),
        report.df.to_json(),
        report.optimize().to_json()
    )



@relatorio_app.callback(
    Output('portfolios_output', 'children'),
    Output('portfolios_chart', 'figure'),
    Input('portfolios_slider', 'value'),
    Input('portfolios_data', 'data'))
def select_portfolio_risk(value, data):
    report = utils.MarkowitzAllocation(data, value)
    return (
        report.table(),
        report.pie()
    )



@relatorio_app.callback(
    Output('corr_timeline_modal', 'is_open'),
    Output('corr_timeline_title', 'children'),
    Output('corr_timeline_chart', 'figure'),
    Input({'ticker_a': ALL, 'ticker_b': ALL}, 'n_clicks'),
    State('dataframe', 'data'),
    prevent_initial_call = True)
def load_corr_timeline(tickers, data):
    if all(click is None for click in tickers):
        raise PreventUpdate
    cc = dash.callback_context.triggered[0]['prop_id'].split('"')
    fig = utils.CorrelationTimeline(cc[3], cc[7])
    
    return (
        True,               # is_open
        fig.title(),        # title
        fig.plot(data)      # chart
    )



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