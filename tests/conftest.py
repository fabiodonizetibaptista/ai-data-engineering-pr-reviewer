import sys
from pathlib import Path


# Adiciona a pasta src ao caminho de importação durante os testes.
# Assim podemos importar providers, reviewer e demais módulos
# sem instalar o projeto como um pacote Python.
SRC_PATH = Path(__file__).resolve().parents[1] / "src"

sys.path.insert(
    0,
    str(SRC_PATH),
)