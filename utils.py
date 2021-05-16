import yfinance
import pandas as pd
import dash_html_components as html



def get_name(ticker:str, b3:bool) -> str:
    '''
    Valida o ticker desejado e retorna seu nome.

    Parameters
    ----------
    ticker : str
        Ticker desejado.
    b3 : bool
        True, se o ticker é negociado na B3;
        False, caso contrário.

    Returns
    -------
    str
        Nome do ticker desejado.

    -------------------------------------------------------------------------- 
    '''

    if b3:
        ticker = f'{ticker}.SA'
    try:
        t = yfinance.Ticker(ticker)
        return t.info['longName'] if 'longName' in t.info else t.info['shortName']
    except:
        return 'Ticker não encontrado'
        


def get_data(ticker:str) -> pd.DataFrame:
    '''
    Retorna o histórico de cotações do ticker desejado.

    Parameters
    ----------
    ticker : str
        Ticker desejado.

    Returns
    -------
    pandas.core.frame.DataFrame
        Histórico de fechamento do ticker desejado.

    --------------------------------------------------------------------------
    '''

    t = yfinance.Ticker(ticker)
    df = t.history(
        period = '5y',
        interval = '1mo',
        auto_adjust = True
    )
    return df.loc[df.Volume > 0, 'Close']



def get_url_hash(tickers:list, b3:list, names:list) -> str:
    '''
    Converte os valores da tabela de inserção em uma lista de hashtags que
    será enviada para a página de análises.

    Parameters
    ----------
    tickers : list of str
        Lista dos tickers nos campos de input de texto.
    b3 : list of bool
        Lista dos checkboxes.
    names : list of str
        Lista dos nomes validados pela função `get_names`.

    Returns
    -------
    str
        Lista de tickers formatada como argumentos de URL.

    --------------------------------------------------------------------------
    '''
    
    df = pd.DataFrame({
        'b3': b3,
        'tickers': tickers,
        'names': names
    })
    
    df = df[~df.names.isin([None, 'Ticker não encontrado'])]
    df.tickers = df.tickers.str.upper()
    
    tickers = df.apply(
        lambda row: f'#{row.tickers}.SA' if row.b3 else f'#{row.tickers}',
        axis = 1
    )

    return ''.join(tickers)



def load_report(hashtags:str) -> list:
    '''
    Captura as hashtags da URL e as utiliza como parâmetro para carregar o
    relatório de análise de diversificação.

    Parameters
    ----------
    hashtags : str
        Hashtags capturadas da URL.

    Returns
    -------
    list of Dash Components
        Relatório de diversificação em formato HTML.

    --------------------------------------------------------------------------
    '''

    tickers = hashtags.split('#')
    return [html.P(ticker) for ticker in tickers]