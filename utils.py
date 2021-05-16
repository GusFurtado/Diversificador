import yfinance
import pandas as pd
import dash_html_components as html



class Ticker:
    '''
    Captura as informações e histórico de cotações do ticker desejado.

    Parameters
    ----------
    ticker : str
        Ticker da ação.
    b3 : bool (default=True)
        True, se for uma ação da B3.
        False, caso contrário.

    Attributes
    ----------
    info : dict
        Conjunto completo de informações do ticker.
    name : str
        Nome completo do ticker.
    currency : str
        Moeda da cotação.
    logo : str
        Logo do ticker.

    --------------------------------------------------------------------------
    '''

    def __init__(self, ticker:str, b3=True):
        if b3:
            ticker = f'{ticker}.SA'
        t = yfinance.Ticker(ticker)
        self.info = t.info
        self.name = t.info['longName'] if 'longName' in t.info else t.info['shortName']
        self.currency = t.info['currency']
        self.logo = t.info['logo_url']



def get_data(ticker):
    t = yfinance.Ticker(ticker)
    df = t.history(
        period = '5y',
        interval = '1mo',
        auto_adjust = True
    )
    return df.loc[df.Volume > 0, 'Close']



def get_url_hash(tickers, b3, names):
    
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



def load_report(hashtags):
    tickers = hashtags.split('#')
    return [html.P(ticker) for ticker in tickers]