from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <html>
        <head>
            <title>FynanPro - Funcionando!</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .success { color: green; font-size: 24px; }
                .info { color: #666; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1 class="success">🎉 FynanPro está funcionando!</h1>
            <p class="info">Sistema básico operacional</p>
            <p><a href="/test">Testar rota adicional</a></p>
        </body>
    </html>
    '''

@app.route('/test')
def test():
    return '''
    <html>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>✅ Teste OK!</h2>
            <p>Todas as rotas funcionando</p>
            <p><a href="/">Voltar</a></p>
        </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'Sistema funcionando perfeitamente'}

if __name__ == '__main__':
    app.run(debug=True)
