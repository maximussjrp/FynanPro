"""
FynanPro App - Teste de nome diferente
"""
from flask import Flask

print("TESTE: Criando app Flask...")
application = Flask(__name__)
print(f"TESTE: App criado: {application}")

@application.route('/')
def hello():
    return "Hello from FynanPro!"

print("TESTE: Rota adicionada")
print(f"TESTE: application final: {application}")
