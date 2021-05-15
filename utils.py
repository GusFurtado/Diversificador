import yfinance



def get_data(ticker:str):
    yfinance.Ticker(ticker)
    return