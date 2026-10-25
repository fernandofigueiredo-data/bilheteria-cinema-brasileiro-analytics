import dash
import dash_bootstrap_components as dbc

from design.tokens import FONTE, MODO_PADRAO, css_variaveis

FONT_AWESOME = ["https://use.fontawesome.com/releases/v5.10.2/css/all.css"]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, FONTE['url'], *FONT_AWESOME],
                title="Bilheteria Diária – Brasil")

# Variáveis CSS geradas dos tokens antes do assets/styles.css; o tema inicial já vem no <html>
app.index_string = f'''<!DOCTYPE html>
<html lang="pt-BR" data-theme="{MODO_PADRAO}">
    <head>
        {{%metas%}}
        <title>{{%title%}}</title>
        {{%favicon%}}
        <style>{css_variaveis()}</style>
        {{%css%}}
    </head>
    <body>
        {{%app_entry%}}
        <footer>
            {{%config%}}
            {{%scripts%}}
            {{%renderer%}}
        </footer>
    </body>
</html>'''

app.scripts.config.serve_locally = True
server = app.server
