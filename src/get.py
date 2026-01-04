from DadosAbertosBrasil import selic, bacen
import pandas as pd
from datetime import date
import yfinance


def get_selic() -> float:
    """Captura a atual taxa SELIC mensal para usá-la como taxa risk-free.

    Returns
    -------
    float
        Taxa SELIC mensal.

    """

    ao_ano = selic(ultimos=1).loc[0, "valor"]
    return (float(ao_ano) / 100 + 1) ** (1 / 12) - 1


def get_dolar():
    """Dólar comercial dos últimos 5 anos agrupados por mês.

    Returns
    -------
    pd.DataFrame
        DataFrame com o valor do dólar comercial agrupado por mês.

    """

    hoje = date.today()
    cinco_anos_atras = hoje.replace(year=hoje.year - 5)

    df: pd.DataFrame = bacen.cambio(inicio=cinco_anos_atras, index=True)
    return df.groupby(df.index.strftime("%Y-%m")).last()


def get_tickers(tickers: list[str]) -> pd.DataFrame:
    """Captura os preços ajustados de fechamento dos tickers fornecidos.

    Parameters
    ----------
    tickers : list[str]
        Lista de tickers a serem capturados.

    Returns
    -------
    pd.DataFrame
        DataFrame com os preços ajustados de fechamento dos tickers.

    """

    t = yfinance.Tickers(" ".join(tickers))
    df = t.history(period="5y", auto_adjust=True, progress=False)
    assert df is not None, "Erro ao capturar os dados dos tickers."

    # Calcular retorno mensal
    close = df["Close"]
    return close.groupby(close.index.strftime("%Y-%m")).last()
