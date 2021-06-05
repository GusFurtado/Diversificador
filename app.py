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
import app_config as cfg
import utils



server = flask.Flask(__name__)
server.secret_key = cfg.SECRET_KEY
pio.templates.default = cfg.PLOTLY_TEMPLATE



tickers_app = dash.Dash(
    __name__,
    server = server,
    url_base_pathname = '/tickers/',
    external_stylesheets = [
        dbc.themes.BOOTSTRAP,
        cfg.MONTSERRAT,
        cfg.FONTAWESOME
    ]
)

tickers_app.title = cfg.NAME
tickers_app.layout = tickers.layout



relatorio_app = dash.Dash(
    __name__,
    server = server,
    url_base_pathname = '/relatorio/',
    external_stylesheets=[dbc.themes.BOOTSTRAP, cfg.MONTSERRAT]
)

relatorio_app.title = cfg.NAME
relatorio_app.layout = relatorio.layout



@server.route('/')
def redirect_menu():
    return flask.redirect('/tickers/')

@server.route('/tickers/')
def render_tickers():
    return flask.redirect('/PyTickers')

@server.route('/relatorio/')
def render_relatorio():
    return flask.redirect('/PyRelatorio')



@tickers_app.callback(
    Output('container', 'n_clicks'),
    Input('container', 'style'))
def clear_flask_session_on_init(_):
    flask.session.clear()
    raise PreventUpdate



@tickers_app.callback(
    Output({'type': 'name', 'uid': MATCH}, 'children'),
    Output({'type': 'button', 'uid': MATCH}, 'color'),
    Output({'type': 'button', 'uid': MATCH}, 'children'),
    Input({'type': 'button', 'uid': MATCH}, 'n_clicks'),
    State({'type': 'input', 'uid': MATCH}, 'value'),
    State({'type': 'checkbox', 'uid': MATCH}, 'checked'),
    prevent_initial_call = True)
def set_name(_, ticker, b3):
    ticker = ticker.upper()
    if b3:
        ticker = f'{ticker}.SA'
    name, color, status = utils.check_ticker(ticker)
    cc = dash.callback_context.triggered[0]['prop_id'].split('"')[7]
    if color == 'success':
        flask.session[cc] = f'#{ticker}'
    else:
        flask.session.pop(cc, None)
    return name, color, status



@tickers_app.callback(
    Output('location', 'href'),
    Input('analyse_portfolio_button', 'n_clicks'),
    State({'type': 'input', 'uid': ALL}, 'value'),
    State({'type': 'checkbox', 'uid': ALL}, 'checked'),
    prevent_initial_call = True)
def go_to_report(_, tickers, b3):
    hashs = ''.join(flask.session.values())
    return f'http://{gethostname()}:{cfg.PORT}/relatorio/{hashs}'



@relatorio_app.callback(
    Output('corr_table', 'children'),
    Output('efficiency_frontier', 'figure'),
    Output('dataframe', 'data'),
    Output('portfolios_data', 'data'),
    Input('location', 'hash'))
def load_relatorio(hashtags):
    report = utils.Markowitz(hashtags)
    return (
        report.corr_table(),
        report.efficiency_frontier(),
        report.df.to_json(),
        report.portfolios.to_json()
    )



@relatorio_app.callback(
    Output('portfolios_returns', 'children'),
    Output('portfolios_chart', 'figure'),
    Input('efficiency_frontier', 'clickData'),
    Input('portfolios_data', 'data'))
def select_portfolio_risk(click, data):
    if click is None:
        value = 0
    else:
        value = click['points'][0]['pointNumber']
    report = utils.MarkowitzAllocation(data, value)
    return (
        report.expected_returns(),
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
        True,
        fig.title(),
        fig.plot(data)
    )



app = DispatcherMiddleware(server, {
    '/PyTickers': tickers_app.server,
    '/PyRelatorio': relatorio_app.server,
})



if __name__ == '__main__':
    run_simple(
        hostname = '0.0.0.0',
        port = cfg.PORT,
        application = app
    )