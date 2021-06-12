from DadosAbertosBrasil import selic 

import json

import dash_bootstrap_components as dbc
import dash_html_components as html

import cvxopt as opt
from cvxopt import blas, solvers
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yfinance



solvers.options['show_progress'] = False



GRAPH_CONFIG = {
    'scrollZoom': False,
    'displayModeBar': False,
    'locale': 'pt'
}



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
            bordered = True
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



class CorrelationTimeline:
    '''
    Carrega toda a estrutura do modal de comparação dos históricos de dois
    tickers diferentes.

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
        Gera uma timeline de cotações de um ticker (quando o valor de ticker_a
        for igual ao ticker_b) ou dois tickers (quando ticker_a e ticker_b
        forem diferentes).

        Parameters
        ----------
        data : dict
            Histórico de cotações dos tickers.

        Returns
        -------
        plotly.graph_objects.Figure
            Gráfico de linhas com histórico de cotações de um ou dois tickers.

        ----------------------------------------------------------------------
        '''

        if self.ticker_a == self.ticker_b:
            fig = self.plot_single(data)
        else:
            fig = self.plot_multi(data)

        fig.update_layout(
            margin = {'b': 10, 't': 10},
            showlegend = False
        )

        return fig
    

    def plot_single(self, data:dict) -> go.Figure:
        '''
        Gera o gráfico de timeline de um ticker.

        Parameters
        ----------
        data : dict
            Histórico de cotações dos tickers.

        Returns
        -------
        plotly.graph_objects.Figure
            Gráfico de linhas com histórico de cotações de um ticker.

        ----------------------------------------------------------------------
        '''

        ds = pd.read_json(data)[self.ticker_a]
        ds = ds.dropna()

        return go.Figure(
            data = go.Scatter(
                x = ds.index,
                y = ds,
                name = self.ticker_a,
                hoverinfo = 'skip'
            )
        )



    def plot_multi(self, data:dict) -> go.Figure:
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

        if self.ticker_a == self.ticker_b:
            return html.Span(
                self.ticker_a,
                className = 'corr_title blue'
            )
        else:
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
        self.p = portfolio
        self.portfolios = pd.read_json(data).round(3)
        self.portfolio = self.portfolios.iloc[portfolio,:]


    def efficiency_frontier(self):
        text = [f'<b>Retorno Esperado:</b> {100*y:.1f}%<br><b>Risco:</b> ±{100*x:.1f}%' \
            for x, y in zip(self.portfolios['Risco'], self.portfolios['Retorno Esperado'])]
        
        marker_color = ['yellow' if n==self.p else 'cyan' \
            for n in range(101)]
        marker_size = [12 if n==self.p else 8 for n in range(101)]
        
        return go.Figure(
            data = go.Scatter(
                x = self.portfolios['Risco'],
                y = self.portfolios['Retorno Esperado'],
                name = 'Fronteira da Eficiência',
                mode = 'markers',
                marker = {
                    'size': marker_size,
                    'color': marker_color,
                    'opacity': 1,
                    'line': {
                        'color': 'blue',
                        'width': 2
                    }
                },
                hovertext = text,
                hoverinfo = 'text'
            ),
            layout = {
                'margin': {'b': 10, 't': 10},
                'xaxis': {
                    'tickformat': ',.1%',
                    'title': {'text': 'Risco'}
                },
                'yaxis': {
                    'tickformat': ',.1%',
                    'title': {'text': r'Retorno Esperado (% a.m.)'}
                },
            }
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
                labels = self.portfolio.index[:-2],
                values = self.portfolio[:-2],
                hole = 0.4,
                textinfo = 'label+percent',
                hoverinfo = 'skip'
            ),
            layout = go.Layout(
                margin = {'b': 0, 't': 0}
            )
        )


    def expected_returns(self):
        '''
        Retorno e risco esperado para o portfólio selecionado.

        Returns
        -------
        list of dash_html_components
            Risco e retorno esperado em formato HTML.

        ----------------------------------------------------------------------
        '''

        return [
            html.B(
                f'{100*self.portfolio[-2]:.1f}% a.m.',
                style = {'font-size': 24}    
            ),
            html.Span(
                f'(±{100*self.portfolio[-1]:.1f}%)',
                style = {'font-size': 16},
                className = 'ml-2'
            )
        ]



class CapitalAllocation:
    '''
    Gera o relatório de alocação de renda risk-free.

    Parameters
    ----------
    data : dict
        Dados do portfólio selecionado.

    Attributes
    ----------
    selic : float
        Taxa SELIC mensal.

    --------------------------------------------------------------------------
    '''


    def __init__(self, data:dict):
        self.data = json.loads(data)
        self.get_selic()

    
    def get_selic(self):
        '''
        Captura a atual taxa SELIC mensal para usá-la como taxa risk-free.

        ----------------------------------------------------------------------
        '''

        ao_ano = selic(ultimos=1).loc[0,'valor']
        self.selic = (float(ao_ano)/100 + 1)**(1/12) - 1


    def capital_allocation_line(self, selected_portfolio:int) -> go.Figure:
        '''
        Gera um gráfico de alocação de capital risk-free.

        Returns
        -------
        plotly.graph_objects.Figure
            Capital Allocation Line

        ----------------------------------------------------------------------
        '''

        razao = [i/20 for i in range(21)]
        retorno = [
            self.weigh_risk_free(
                value = self.data['Retorno Esperado'],
                risk_free_rate = self.selic,
                p = p
            ) for p in razao
        ]
        risco = [
            self.weigh_risk_free(
                value = self.data['Risco'],
                risk_free_rate = 0,
                p = p
            ) for p in razao
        ]
        text = [
            f'<b>Proporção de Renda Fixa:</b> {100*ra:.1f}%<br>' \
            + f'<b>Retorno Esperado:</b> {100*re:.1f} ± {100*ri:.1f}% a.m.' \
            for ra, re, ri in zip(razao, retorno, risco)
        ]

        marker_color = ['yellow' if n==selected_portfolio else 'cyan' \
            for n in range(21)]
        marker_size = [12 if n==selected_portfolio else 8 for n in range(21)]

        return go.Figure(
            data = go.Scatter(
                x = razao,
                y = retorno,
                mode = 'lines+markers',
                hovertext = text,
                hoverinfo = 'text',
                marker = {
                    'size': marker_size,
                    'color': marker_color,
                    'opacity': 1,
                    'line': {
                        'color': 'blue',
                        'width': 2
                    }
                },
                line = {
                    'color': 'blue',
                    'width': 3
                }
            ),
            layout = {
                'margin': {'b': 10, 't': 10},
                'xaxis': {
                    'tickformat': ',.1%',
                    'autorange': 'reversed',
                    'title': {'text': 'Proporção de Renda Fixa'}
                },
                'yaxis': {
                    'tickformat': ',.1%',
                    'title': {'text': r'Retorno Esperado (% a.m.)'}
                },
            }
        )


    def final_table(self, p:float) -> list:

        def tr(ticker):
            value = self.weigh_risk_free(
                value = self.data[ticker],
                risk_free_rate = 0,
                p = p
            )
            return html.Tr([
                html.Td(ticker),
                html.Td(f'{100*value:.1f}%')
            ])

        renda_fixa = [
            html.Td('Renda Fixa'),
            html.Td(f'{100*p:.1f}%')    
        ]

        renda_variavel = [tr(ticker) for ticker in self.data \
            if ticker not in ['Retorno Esperado', 'Risco']]

        return renda_fixa + renda_variavel


    def weigh_risk_free(
            self,
            value: float,
            risk_free_rate: float,
            p: float
        ) -> float:
        '''
        Adiciona o peso da taxa risk-free a uma variável.

        Parameters
        ----------
        value : float
            Valor da variável que será ponderada.
        risk_free_rate : float
            Valor da taxa risk-free.
        p : float
            Proporção da taxa risk-free que será adicionada à variável.

        Returns
        -------
        float
            Valor ponderada para a variável.

        ----------------------------------------------------------------------
        '''

        return p*risk_free_rate + (1-p)*value


    def expected_returns(self, p:float) -> list:
        '''
        Retorno e risco esperado para o portfólio selecionado.

        Parameters
        ----------
        p : float
            Proporção da taxa risk-free que será adicionada à variável.

        Returns
        -------
        list of dash_html_components
            Risco e retorno esperado em formato HTML.

        ----------------------------------------------------------------------
        '''

        retorno = 100 * self.weigh_risk_free(
            value = self.data['Retorno Esperado'],
            risk_free_rate = self.selic,
            p = p
        )

        risco = 100 * self.weigh_risk_free(
            value = self.data['Risco'],
            risk_free_rate = 0,
            p = p
        )

        return [
            html.B(
                f'{retorno:.1f}% a.m.',
                style = {'font-size': 24}    
            ),
            html.Span(
                f'(±{risco:.1f}%)',
                style = {'font-size': 16},
                className = 'ml-2'
            )
        ]
