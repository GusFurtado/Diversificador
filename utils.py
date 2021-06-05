import dash_bootstrap_components as dbc
import dash_html_components as html

import cvxopt as opt
from cvxopt import blas, solvers
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yfinance



solvers.options['show_progress'] = False



def check_ticker(ticker:str) -> str:
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
        color = 'success'
        status = [
            html.I(className='fas fa-check-circle mr-2'),
            html.Span('Ticker validado')
        ]

    except:
        name = 'Ticker não encontrado'
        color = 'danger'
        status = [
            html.I(className='fas fa-times-circle mr-2'),
            html.Span('Tente novamente')
        ]

    return name, color, status



class Markowitz:
    '''
    Captura as hashtags da URL e as utiliza como parâmetro para carregar o
    relatório de análise de diversificação.

    Parameters
    ----------
    hashtags : str
        Hashtags capturadas da URL.

    --------------------------------------------------------------------------
    '''

    def __init__(self, hashtags:list):
        tickers = hashtags.split('#')
        t = yfinance.Tickers(' '.join(tickers))
        
        self.df = t.history(
            period = '5y',
            auto_adjust = True,
            progress = False
        ).Close
        
        self.returns = self.df.groupby(
            self.df.index.strftime('%Y-%m')
        ).last().pct_change().dropna()
        
        self.tickers = self.df.columns
        self.optimize()


    def corr_table(self) -> dbc.Table:
        '''
        Gera uma matriz de correlação em formato HTML.

        Returns
        -------
        dash_bootstrap_components.Table
            Tabela de correlação formatada.

        ----------------------------------------------------------------------
        '''
        
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

        df = self.df.corr().reset_index()
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
            bordered = True,
            className = 'shadow'
        )


    def optimize(self) -> pd.DataFrame:
        '''
        Gera um DataFrame de portfólios otimizados.

        Returns
        -------
        pandas.core.frame.DataFrame
            DataFrame de portfólios.

        ----------------------------------------------------------------------
        '''
        
        # Returns setup
        returns = np.asmatrix(self.returns.T)
        n = len(returns)

        # Optimizer setup
        S = opt.matrix(np.cov(returns))
        pbar = opt.matrix(np.mean(returns, axis=1))
        G = -opt.matrix(np.eye(n))
        h = opt.matrix(0.0, (n ,1))
        A = opt.matrix(1.0, (1, n))
        b = opt.matrix(1.0)

        # Solve
        mus = [10**(t/20-1) for t in range(100)]
        portfolios = [solvers.qp(mu*S, -pbar, G, h, A, b)['x'] for mu in mus]

        # Concatenate porfolios
        concat = np.concatenate([np.asarray(portfolio) for portfolio in portfolios])
        df = pd.DataFrame(concat.reshape(-1,n))
        df.columns = self.tickers

        # Results
        df['Retorno Esperado'] = [blas.dot(pbar, x) for x in portfolios]
        df['Risco'] = [np.sqrt(blas.dot(x, S*x)) for x in portfolios]

        df.index = df.index[::-1]
        self.portfolios = df.sort_index()


    def efficiency_frontier(self):
        return go.Figure(
            go.Scatter(
                x = self.portfolios['Risco'],
                y = self.portfolios['Retorno Esperado'],
                name = 'Fronteira da Eficiência',
                mode = 'markers',
                marker = {
                    'size': 10
                }
            )
        )



class CorrelationTimeline:
    '''
    Carrega toda a estrutura do modal de comparação dos históricos de dois
    tickers  diferentes.

    Parameters
    ----------
    ticker_a : str
        Primeiro ticker que será comparado.
    ticker_b : str
        Segundo ticker que será comparado.

    --------------------------------------------------------------------------
    '''

    def __init__(self, ticker_a:str, ticker_b:str):
        self.ticker_a = ticker_a
        self.ticker_b = ticker_b


    def plot(self, data):
        '''
        Gera o gráfico com as timelines dos dois tickers.

        Parameters
        ----------
        data : dict
            Histórico de cotações dos tickers.

        Returns
        -------
        plotly.graph_objects.Figure
            Gráfico de linhas com histórico de cotações normalizado de dois
            tickers.

        ----------------------------------------------------------------------
        '''

        df = pd.read_json(data)[[self.ticker_a, self.ticker_b]]
        df = df.dropna()

        fig = go.Figure(
            layout = {
                'yaxis': {'visible': False},
                'showlegend': False
            }
        )

        for ticker in [self.ticker_a, self.ticker_b]:

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

        return fig


    def title(self) -> list:
        '''
        Título formatado do gráfico.

        Returns
        -------
        list of Dash components
            Título formatado para o ModalHeader do Dash Bootstrap Components.

        ----------------------------------------------------------------------
        '''

        return [
            html.Span(
                self.ticker_a,
                className = 'corr_title blue'
            ),
            html.Span('  x  '),
            html.Span(
                self.ticker_b,
                className = 'corr_title red'
            )
        ]



class MarkowitzAllocation:
    '''
    Gera o relatório de alocação de recursos.

    Parameters
    ----------
    data : dict
        Tabela de alocação de todos os portfólios.
    portfolio : int
        ID do portfólio deste relatório.

    --------------------------------------------------------------------------
    '''

    def __init__(self, data:dict, portfolio:int):
        self.df = pd.read_json(data)
        self.portfolio = portfolio


    def table(self) -> dbc.Table:
        '''
        Gera uma tabela HTML de alocação de recursos.

        Returns
        -------
        dash_bootstrap_components.Table
            Tabela de alocação de recursos formatada.

        ----------------------------------------------------------------------
        '''

        return go.Figure(
            go.Table(
                header = {'values': ['Recurso', 'Alocação']},
                cells = {'values': [
                    self.df.columns[:-2],
                    self.df.iloc[self.portfolio,:-2].apply(
                        lambda x: f'{100*x:.1f}%'
                    )
                ]}
            )
        )

    
    def pie(self) -> go.Pie:
        '''
        Gráfico de alocação de recursos.

        Returns
        -------
        plotly.graph_objects.Pie
            Pie chart de alocação de recursos.
        
        ----------------------------------------------------------------------
        '''

        return go.Figure(
            data = go.Pie(
                labels = self.df.columns[:-2],
                values = self.df.iloc[self.portfolio,:-2],
                hole = 0.5
            ),
            layout = go.Layout(
                margin = {'b': 20, 't': 20}
            )
        )


    def expected_returns(self):
        return [
            html.B(
                f'{100*self.df.iloc[self.portfolio,-2]:.1f}% a.m.',
                style = {'font-size': 24}    
            ),
            html.Span(
                f'(±{100*self.df.iloc[self.portfolio,-1]:.1f}%)',
                style = {'font-size': 16},
                className = 'ml-2'
            )
        ]