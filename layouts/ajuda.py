import dash_html_components as html
from dash_bootstrap_components import Container



textwall = html.Div([
    html.H1('Diversificador de Portfólio'),
    html.Hr(),
    html.H2(
        'O que é o Diversificador de Portfólio?'
    ),
    html.P('É uma ferramenta que utiliza o histórico de cotações de títulos públicos para identificar a covariância desses títulos e montar uma carteira com a menor variação (risco) possível, dado o retorno desejado.'),
    html.P([
        html.B('DISCLAIMER:'),
        html.Span(' Isto não é uma recomendação de investimentos. Esta é uma ferramenta de análises estatísticas baseada em histórico de cotações. Procure um consultor de valores mobiliários registrado para aconselhamentos financeiros.')
    ]),
    html.Hr(),
    html.H2(
        'Como acessar o Diversificador de Portfólio?',
    ),
    html.P('Ele pode ser acessado pelo seguinte endereço:'),
    html.P(html.A(
        'https://diversificador.herokuapp.com/',
        href = 'https://diversificador.herokuapp.com/'
    )),
    html.Hr(),
    html.H2('Como utilizar o Diversificador de Portfólio?'),
    html.P([
        html.Span('Na página inicial, insira os tickers desejados na caixa e aperte o botão '),
        html.I(className='fas fa-plus-circle'),
        html.Span(' para adicionar. Mantenha o check "B3" selecionado, caso o título seja negociado na B3 e desmarque caso contrário.')
    ]),
    html.P(html.Img(src="https://raw.githubusercontent.com/GusFurtado/Diversificador/main/assets/menu.png")),
    html.P('Assim que todos os tickers forem adicionar, clique no botão "Analisar carteira" para carregar o relatório.'),
    html.Hr(),
    html.H2('Como é feita a otimização do portfólio?'),
    html.P([
        html.Span('O Diversificador de Portfólio utiliza a '),
        html.A(
            'teoria moderna de portfólio',
            href='https://en.wikipedia.org/wiki/Modern_portfolio_theory'
        ),
        html.Span(' desenvolvida inicialmente por '),
        html.A(
            'Harry Markowitz',
            href = 'https://en.wikipedia.org/wiki/Harry_Markowitz'
        ),
        html.Span(', economista americano laureado com o prêmio Nobel em Economia.')
    ]),
    html.P('O algoritmo utiliza otimização convexa para identificar qual é a combinação de títulos que maximiza o retorno esperado dado a variância (risco) que se está disposto a correr.'),
    html.Hr(),
    html.H2('O que é a Matriz de Correlação?'),
    html.P([
        html.Span('É a matriz que apresenta a correlação ('),
        html.A(
            'coeficiente de Pearson',
            href = 'https://en.wikipedia.org/wiki/Pearson_correlation_coefficient'
        ),
        html.Span(') entre todos os pares de títulos possíveis.')
    ]),
    html.Ul([
        html.Li([
            html.Span('Valores próximos de '),
            html.B('1'),
            html.Span(' significam uma alta correlação positiva. Os títulos caminham juntos, quando um cai o outro costuma cair junto.')
        ]),
        html.Li([
            html.Span('Valores próximos de '),
            html.B('-1'),
            html.Span(' significam uma alta correlação negativa. Quando um cai, o outro sobe e vice-versa.')
        ]),
        html.Li([
            html.Span('Valores próximos de '),
            html.B('0'),
            html.Span(' significam que os títulos não tem correlação. Um é independente do outro.')
        ])
    ]),
    html.P('O objetivo da otimização é dar um maior peso a títulos de baixa correlação, onde a variância de um cancela a variância de outro, de forma que a variância geral da carteira seja minimizada.'),
    html.P(html.Img(src='https://raw.githubusercontent.com/GusFurtado/Diversificador/main/assets/matriz.png')),
    html.P('Ao clicar nas células da tabela, será aberto um gráfico de cotações normalizado que permite visualizar como esses títulos se comportam em relação um ao outro.'),
    html.P(html.Img(src='https://raw.githubusercontent.com/GusFurtado/Diversificador/main/assets/grafico.png')),
    html.Hr(),
    html.H2('O que é a Fronteira da Eficiência?'),
    html.P('É o conjunto de portfólios que possuem o maior retorno esperado (eixo Y) em função do risco que se está disposto a correr (eixo X).'),
    html.P(html.Img(src='https://raw.githubusercontent.com/GusFurtado/Diversificador/main/assets/variavel.png')),
    html.Hr(),
    html.H2('O que é a Linha de Alocação de Capital?'),
    html.P('É a linha que representa o retorno esperado em função da proporção de títulos sem risco. A ferramenta utiliza a taxa SELIC atual para o cálculo do retorno livre de risco.'),
    html.P(html.Img(src='https://raw.githubusercontent.com/GusFurtado/Diversificador/main/assets/fixa.png')),
    html.Hr(),
    html.H2('Que ferramentas foram utilizadas para a construção do Diversificador de Portfólio?'),
    html.P('Ele foi construído em Python utilizando os seguintes pacote:'),
    html.Ul([
        html.Li([
            html.A(
                html.B('DadosAbertosBrasil'),
                href = 'https://www.gustavofurtado.com/dab.html'
            ),
            html.Span(' para coleta das taxas de câmbio e SELIC;')
        ]),
        html.Li([
            html.A(
                html.B('yfinance'),
                href = 'https://aroussi.com/post/python-yahoo-finance'
            ),
            html.Span(' para coleta de dados da API do '),
            html.A(
                'Yahoo! Finance',
                href = 'https://finance.yahoo.com/'
            ),
            html.Span(';')
        ]),
        html.Li([
            html.A(
                html.B('CVXOPT'),
                href = 'https://cvxopt.org/'
            ),
            html.Span(' para otimização convexa;')
        ]),
        html.Li([
            html.A(
                html.B('Dash'),
                href = 'https://plotly.com/dash/'
            ),
            html.Span(' para construção da estrutura HTML e interface do usuário;')
        ]),
        html.Li([
            html.A(
                html.B('Plotly'),
                href = 'https://plotly.com/python/'
            ),
            html.Span(' para os gráficos.')
        ])
    ]),
    html.Hr(),
    html.H2('Como posso contribuir para o projeto?'),
    html.P('O código está aberto, então sinta-se a vontade para propor melhorias.'),
    html.P('Caso queira ajudar a pagar um domínio e um servidor para hospedar esta aplicação, você pode transferir para a seguinte chave PIX:'),
    html.P(html.B('54a9544a-786e-4a29-9421-4a6864dd0cca'))
])



layout = Container(
    textwall,
    className = 'shadow mt-4'
)