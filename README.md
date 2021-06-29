# Diversificador de Portfólio

## O que é o Diversificador de Portfólio?

É uma ferramenta que utiliza o histórico de cotações de títulos públicos para identificar a covariância desses títulos e montar uma carteira com a menor variação (risco) possível, dado o retorno desejado.

**DISCLAIMER:** Isto não é uma recomendação de investimentos. Esta é uma ferramenta de análises estatísticas baseada em histórico de cotações. Procure um consultor de valores mobiliários registrado para aconselhamentos financeiros.

## Como acessar o Diversificador de Portfólio?

Ele pode ser acessado pelo seguinte endereço:

https://diversificador.herokuapp.com/

## Como utilizar o Diversificador de Portfólio?

Na página inicial, insira os tickers desejados na caixa e aperte o botão (+) para adicionar. Mantenha o check "B3" selecionado, caso o título seja negociado na B3 e desmarque caso contrário.

<img src="https://raw.githubusercontent.com/GusFurtado/Diversificador/main/assets/menu.png">

Assim que todos os tickers forem adicionar, clique no botão "Analisar carteira" para carregar o relatório.

## Como é feita a otimização do portfólio?

O Diversificador de Portfólio utiliza a [teoria moderna de portfólio](https://en.wikipedia.org/wiki/Modern_portfolio_theory) desenvolvida inicialmente por [Harry Markowitz](https://en.wikipedia.org/wiki/Harry_Markowitz), economista americano laureado com o prêmio Nobel em Economia.

O algoritmo utiliza otimização convexa para identificar qual é a combinação de títulos que maximiza o retorno esperado dado a variância (risco) que se está disposto a correr.

## O que é a Matriz de Correlação?

É a matriz que apresenta a correlação ([coeficiente de Pearson](https://en.wikipedia.org/wiki/Pearson_correlation_coefficient)) entre todos os pares de títulos possíveis.

- Valores próximos de **1** significam uma alta correlação positiva. Os títulos caminham juntos, quando um cai o outro costuma cair junto.
- Valores próximos de **-1** significam uma alta correlação negativa. Quando um cai, o outro sobe e vice-versa.
- Valores próximos de **0** significam que os títulos não tem correlação. Um é independente do outro.

O objetivo da otimização é dar um maior peso a títulos de baixa correlação, onde a variância de um cancela a variância de outro, de forma que a variância geral da carteira seja minimizada.

<img src="https://raw.githubusercontent.com/GusFurtado/Diversificador/main/assets/matriz.png">

Ao clicar nas células da tabela, será aberto um gráfico de cotações normalizado que permite visualizar como esses títulos se comportam em relação um ao outro.

<img src="https://raw.githubusercontent.com/GusFurtado/Diversificador/main/assets/grafico.png">

## O que é a Fronteira da Eficiência?

É o conjunto de portfólios que possuem o maior retorno esperado (eixo Y) em função do risco que se está disposto a correr (eixo X).

<img src="https://raw.githubusercontent.com/GusFurtado/Diversificador/main/assets/variavel.png">


## O que é a Linha de Alocação de Capital?

É a linha que representa o retorno esperado em função da proporção de títulos sem risco. A ferramenta utiliza a taxa SELIC atual para o cálculo do retorno livre de risco.

<img src="https://raw.githubusercontent.com/GusFurtado/Diversificador/main/assets/fixa.png">

## Que ferramentas foram utilizadas para a construção do Diversificador de Portfólio?

Ele foi construído em Python utilizando os seguintes pacote:
- [DadosAbertosBrasil](https://www.gustavofurtado.com/dab.html) para coleta das taxas de câmbio e SELIC;
- [yfinance](https://aroussi.com/post/python-yahoo-finance) para coleta de dados da API do [Yahoo! Finance](https://finance.yahoo.com/);
- [CVXOPT](https://cvxopt.org/) para otimização convexa; 
- [Dash](https://plotly.com/dash/) para construção da estrutura HTML e interface do usuário;
- [Plotly](https://plotly.com/python/) para os gráficos.

## Como posso contribuir para o projeto?

O código está aberto, então sinta-se a vontade para propor melhorias.

Caso queira ajudar a pagar um domínio e um servidor para hospedar esta aplicação, você pode transferir para a seguinte chave PIX:

**54a9544a-786e-4a29-9421-4a6864dd0cca**