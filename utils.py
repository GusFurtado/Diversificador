import dash_bootstrap_components as dbc
import dash_html_components as html

import yfinance



GRAPH_CONFIG = {
    'scrollZoom': False,
    'displayModeBar': False,
    'locale': 'pt'
}



def get_ticker_name(ticker:str) -> str:
    '''
    Valida o ticker desejado e retorna seu nome.

    Parameters
    ----------
    ticker : str
        Ticker desejado, adicionado o prefixo ".SA" caso seja uma ação
        negociada na Bolsa de Valores de São Paulo.

    Returns
    -------
    str
        Nome do ticker desejado.
    str
        Nova cor do botão de verificação:
        - 'success' (verde), se validado;
        - 'danger' (vermelho), em caso de falha.
    list of dash_html_components
        Novo ícone e texto do botão de verificação.

    -------------------------------------------------------------------------- 
    '''

    try:
        t = yfinance.Ticker(ticker)
        name = t.info['longName'] if 'longName' in t.info else t.info['shortName']
        color = 'primary'
        status = 'Ticker inserido'

    except:
        name = f'Ticker "{ticker}" não encontrado'
        color = 'danger'
        status = 'Erro! Tente novamente'

    return name, color, status



def tag(ticker:str):
    return dbc.Badge([
        html.Span(
            ticker,
            style = {'font-size': 16}
        ),
        html.I(
            className = 'fas fa-times ml-3',
            style = {'cursor': 'pointer'},
            id = {'ticker_remove': ticker},
            n_clicks_timestamp = 0
        )
    ],
        pill = True,
        color = 'primary',
        style = {'padding': 10},
        className = 'shadow'
    )



def menu_ajuda(position):
    return html.A([
        html.I(
            className = 'fas fa-question-circle mr-2',
        ),
        html.Span(html.B('Ajuda'))
    ],
        href = '/ajuda',
        target = '_blank',
        style = {
            'font-size': 20,
            'color': 'white',
            'top': 10,
            'right': 20,
            'position': position
        }
    )