import dash_bootstrap_components as dbc
import dash_html_components as html

import pandas as pd
import plotly.graph_objects as go
import yfinance



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



class Markowitz:
    '''
    Captura as hashtags da URL e as utiliza como parâmetro para carregar o
    relatório de análise de diversificação.

    Parameters
    ----------
    hashtags : str
        Hashtags capturadas da URL.

    ------------------------------------------------------------------------
    '''

    def __init__(self, hashtags:list):
        tickers = hashtags.split('#')
        t = yfinance.Tickers(' '.join(tickers))
        self.df = t.history(
            period = '5y',
            auto_adjust = True,
            progress = False
        ).Close


    def corr(self) -> pd.DataFrame:
        '''
        Gera a matriz de correlação dos tickers.

        Returns
        -------
        pandas.core.frame.DataFrame
            Matriz de correlação (coeficiente de Pearson) entre os tickers.

        ----------------------------------------------------------------------
        '''
        return self.df.corr().reset_index()


    def corr_table(self) -> dbc.Table:
        
        def _table_head(th):
            if th == 'index':
                th = ''
            return html.Th(
                th,
                className = 'corr_table_head'    
            )

        def _table_data(td, i, j):
            if isinstance(td, str):
                return html.Td(
                    html.B(td)
                )
            else:
                if td == 1:
                    style = {
                        'background-color': 'black',
                        'color': 'black'
                    }
                elif td > 0.7:
                    style = {
                        'background-color': 'crimson',
                        'color': 'white'
                    }
                elif td < 0.1:
                    style = {
                        'background-color': 'aqua',
                        'color': 'black'
                    }
                else:
                    style = None
                return html.Td(
                    f'{td:.2f}',
                    className = 'corr_table_data',
                    style = style,
                    id = {
                        'ticker_a': df.iat[i,0],
                        'ticker_b': df.columns[j]
                    }
                )

        df = self.corr()
        return dbc.Table([
            html.Thead(
                html.Tr([
                    _table_head(th) for th in df.columns
                ])
            ),
            html.Tbody([
                html.Tr([
                    _table_data(td, i, j) for j, td in enumerate(row)
                ]) for i, row in df.iterrows()
            ])
        ],
            bordered = True
        )


    def corr_timeline(self, ticker_a:str, ticker_b:str) -> go.Figure:
        '''
        Gera gráfico de linhas para comparação entre dois tickers.

        Parameters
        ----------
        ticker_a : str
            Primeiro ticker que será comparado.
        ticker_b : str
            Segundo ticker que será comparado.

        Returns
        -------
        plotly.graph_objects.Figure
            Gráfico de linhas com histórico de cotações normalizado de dois tickers.

        --------------------------------------------------------------------
        '''
        df = self.df[[ticker_a, ticker_b]].dropna()

        fig = go.Figure(
            layout = {
                'legend_orientation': 'h',
                'title': {
                    'text': f'<b style="color:blue">{ticker_a}</b> x <b style="color:red">{ticker_b}</b>'},
                'yaxis': {'visible': False},
                'showlegend': False
            }
        )

        for ticker in [ticker_a, ticker_b]:

            # Normalizar histórico do ticker
            ds = (df[ticker] - df[ticker].min()) \
                / (df[ticker].max() - df[ticker].min()) 

            fig.add_trace(
                go.Scatter(
                    x = df.index,
                    y = ds,
                    name = ticker,
                    hoverinfo = 'skip'
                )
            )

        fig.show()