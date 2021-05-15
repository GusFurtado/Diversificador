import dash
import dash_bootstrap_components as dbc

import layout
import utils



MONTSERRAT = {
    'href': 'https://fonts.googleapis.com/css?family=Montserrat',
    'rel': 'stylesheet'
}



app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, MONTSERRAT]
)

app.title = 'Diversificador de Carteira'
app.layout = layout.layout



if __name__ == '__main__':
    app.run_server(
        host = '0.0.0.0',
        port = 1000
    )