print("Hello World - teste básico")

from flask import Flask

print("Flask importado com sucesso")

app = Flask(__name__)

print("App Flask criado")

@app.route('/')
def hello():
    return "Hello World!"

print("Rota adicionada")

if __name__ == '__main__':
    print("Rodando como main")
    print("App final:", app)
else:
    print("Importado como módulo")
    print("App final:", app)
