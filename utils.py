import pandas as pd
import plotly.graph_objects as go
import yfinance



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
    history : pandas.Series
        Histórico de cotações do ticker.
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
        df = t.history(
            period = '5y',
            interval = '1mo',
            auto_adjust = True
        )

        self.history = df.loc[df.Volume > 0, 'Close']
        self.info = t.info
        self.name = t.info['longName']
        self.currency = t.info['currency']
        self.logo = t.info['logo_url']