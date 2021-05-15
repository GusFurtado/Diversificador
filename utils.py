import yfinance
import plotly.graph_objects as go



def get_data(ticker:str, b3=True):
    '''
    Captura o histórico de preço da ação desejada.

    Parameters
    ----------
    ticker : str
        Ticker da ação.
    b3 : bool (default=True)
        True, se for uma ação da B3.
        False, caso contrário.

    Returns
    -------
    pandas.Series
        Histórico de valores de fechamento da ação.

    -------------------------------------------------------------
    '''
    
    if b3:
        ticker = f'{ticker}.SA'
        
    t = yfinance.Ticker(ticker)
    df = t.history(
        period = '5y',
        interval = '1mo',
        auto_adjust = True
    )

    return df.loc[df.Volume > 0, 'Close']



def timeline(ticker, check):
    serie = get_data(ticker, check)
    return go.Figure(
        go.Scatter(
            x = serie.index,
            y = serie,
            mode = 'lines'
        )
    )