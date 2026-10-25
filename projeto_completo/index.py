"""Ponto de entrada (gunicorn index:server). Estrutura: design/ (tokens, formatos, tema Plotly),
dados.py (cálculos), graficos.py e componentes.py (visual), layout.py (página), callbacks.py (interação);
a aba "Recuperação pós-pandemia" usa dados_recuperacao.py, layout_recuperacao.py e callbacks_recuperacao.py."""
from app import app, server  # noqa: F401  (server é usado pelo gunicorn)
import layout
import callbacks  # noqa: F401  (registra os callbacks)
import callbacks_recuperacao  # noqa: F401  (aba Recuperação pós-pandemia)

app.layout = layout.montar

# Run server
if __name__ == '__main__':
    app.run(debug=False)
