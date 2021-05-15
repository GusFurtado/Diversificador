import dash_bootstrap_components as dbc
import dash_html_components as html



main_content = [
    html.H1('Diversificador de Carteira'),
    html.H3('Conteúdo')
]



layout = dbc.Container(
    children = main_content,
    id = 'container'
)