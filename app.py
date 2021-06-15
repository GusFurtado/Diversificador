from socket import gethostname

import dash
from dash.dependencies import Output, Input, State, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

import flask
import plotly.io as pio
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug import run_simple

from layouts import tickers
from layouts import relatorio
import app_config as cfg
import report
import utils



server = flask.Flask(__name__)
server.secret_key = cfg.SECRET_KEY
pio.templates.default = cfg.PLOTLY_TEMPLATE

external_stylesheets = [
    dbc.themes.BOOTSTRAP,
    cfg.MONTSERRAT,
    cfg.FONTAWESOME
]



tickers_app = dash.Dash(
    __name__,
    server = server,
    url_base_pathname = '/tickers/',
    external_stylesheets = external_stylesheets
)

tickers_app.title = cfg.NAME
tickers_app.layout = tickers.layout



relatorio_app = dash.Dash(
    __name__,
    server = server,
    url_base_pathname = '/relatorio/',
    external_stylesheets = external_stylesheets
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
    Output('ticker_data', 'data'),
    Output('ticker_toast', 'children'),
    Output('ticker_toast', 'header'),
    Output('ticker_toast', 'icon'),
    Output('ticker_toast', 'is_open'),
    Output('ticker_input', 'value'),
    Input('ticker_add', 'n_clicks'),
    Input({'ticker_remove': ALL}, 'n_clicks_timestamp'),
    State('ticker_input', 'value'),
    State('ticker_checkbox', 'checked'),
    State('ticker_data', 'data'),
    prevent_initial_call = True)
def add_ticker_to_data(_, clicks, ticker, b3, data):

    # Remover ticker
    cc = dash.callback_context.triggered[0]['prop_id']
    if cc != 'ticker_add.n_clicks':
        ticker_to_remove = cc.split('"')[3]
        data.pop(clicks.index(max(clicks)))
        return (
            data,
            f'Ticker "{ticker_to_remove}" removido da carteira.',
            'Ticker removido',
            'danger',
            True,
            dash.no_update
        )

    # Formatar ticker
    ticker = ticker.upper()
    if b3 and not ticker.endswith('.SA'):
        ticker = f'{ticker}.SA'

    # Adicionar ticker
    if ticker in data:
        full_name = f'Ticker "{ticker}" já está na carteira.'
        color = 'danger'
        header = 'Erro! Tente novamente.'
    else:
        full_name, color, header = utils.get_ticker_name(ticker)
    
    if color == 'primary':
        data.append(ticker)
        value = None
    else:
        data = dash.no_update
        value = dash.no_update
    
    return data, full_name, header, color, True, value



@tickers_app.callback(
    Output('ticker_tags', 'children'),
    Output('ticker_analyse', 'disabled'),
    Input('ticker_data', 'data'))
def generate_tags(data):
    tags = [
        dbc.Col(
            utils.tag(ticker),
            width = 'auto',
            className = 'mb-3'
        ) for ticker in data
    ]
    return tags, len(data)<2



@tickers_app.callback(
    Output('location', 'href'),
    Input('ticker_analyse', 'n_clicks'),
    State('ticker_data', 'data'),
    prevent_initial_call = True)
def go_to_report(_, data):
    hashs = ''.join([f'#{d}' for d in data])
    return f'http://{gethostname()}:{cfg.PORT}/relatorio/{hashs}'



@relatorio_app.callback(
    Output('corr_table', 'children'),
    Output('monthly_returns', 'data'),
    Output('portfolios_data', 'data'),
    Input('location', 'hash'))
def load_relatorio(hashtags):
    r = report.Markowitz(hashtags)
    return (
        r.corr_table(),
        r.df.to_json(),
        r.portfolios.to_json()
    )



@relatorio_app.callback(
    Output('portfolios_returns', 'children'),
    Output('portfolios_chart', 'figure'),
    Output('selected_portfolio', 'data'),
    Output('efficiency_frontier', 'figure'),
    Input('efficiency_frontier', 'clickData'),
    Input('portfolios_data', 'data'))
def select_portfolio_risk(click, data):
    portfolio = 0 if click is None else click['points'][0]['pointNumber']
    r = report.MarkowitzAllocation(data, portfolio)
    return (
        r.expected_returns(),
        r.pie(),
        r.portfolio.to_json(),
        r.efficiency_frontier()
    )



@relatorio_app.callback(
    Output('capital_allocation_line', 'figure'),
    Output('risk_free_returns', 'children'),
    Output('risk_free_table', 'children'),
    Input('selected_portfolio', 'data'),
    Input('capital_allocation_line', 'clickData'),
    prevent_inital_call = True)
def update_capital_allocation_line(data, click):
    p = 0 if click is None else click['points'][0]['pointNumber']
    r = report.CapitalAllocation(data)
    return (
        r.capital_allocation_line(p),
        r.expected_returns(p/20),
        r.final_table(p/20)
    )



@relatorio_app.callback(
    Output('corr_timeline_modal', 'is_open'),
    Output('corr_timeline_title', 'children'),
    Output('corr_timeline_chart', 'figure'),
    Input({'ticker_a': ALL, 'ticker_b': ALL}, 'n_clicks'),
    State('monthly_returns', 'data'),
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