# FynanPro - Sistema de Planejamento Financeiro

FynanPro é uma aplicação web completa para gestão e planejamento financeiro pessoal, desenvolvida em Python com Flask.

## 🚀 Características Principais

- **Dashboard Intuitivo**: Visão geral das finanças com gráficos e indicadores
- **Gestão de Transações**: Adicione, edite e categorize receitas e despesas
- **Categorização Inteligente**: Sistema avançado de categorização de gastos
- **Análise Financeira**: Relatórios detalhados e análise de saúde financeira
- **Planejamento**: Ferramentas para planejamento financeiro futuro
- **Sistema de Assinatura**: Planos mensais, semestrais e anuais
- **Suporte Integrado**: Sistema de chat para atendimento ao cliente
- **Painel Administrativo**: Gestão completa de usuários e sistema

## 🛠️ Tecnologias Utilizadas

- **Backend**: Python 3.x + Flask
- **Banco de Dados**: SQLAlchemy + SQLite
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Autenticação**: Flask-Login + bcrypt
- **Pagamentos**: Stripe API
- **Outras**: WTForms, Email-Validator

## 📦 Instalação

### Pré-requisitos
- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

### Passos de Instalação

1. **Clone o repositório**
   ```bash
   git clone https://github.com/seu-usuario/fynanpro.git
   cd fynanpro
   ```

2. **Crie um ambiente virtual**
   ```bash
   python -m venv .venv
   ```

3. **Ative o ambiente virtual**
   - Windows:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - Linux/macOS:
     ```bash
     source .venv/bin/activate
     ```

4. **Instale as dependências**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure o banco de dados**
   ```bash
   python init_db.py
   ```

6. **Execute a aplicação**
   ```bash
   python app.py
   ```

A aplicação estará disponível em `http://localhost:5000`

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
SECRET_KEY=sua-chave-secreta-muito-segura
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
DATABASE_URL=sqlite:///finance_planner_saas.db
```

### Configuração do Stripe

1. Crie uma conta no [Stripe](https://stripe.com)
2. Obtenha suas chaves de API (pública e secreta)
3. Configure as chaves no arquivo `.env` ou `config.py`

## 📋 Funcionalidades

### Para Usuários
- ✅ Cadastro e login seguro
- ✅ Dashboard com resumo financeiro
- ✅ Adicionar/editar/excluir transações
- ✅ Categorização de gastos
- ✅ Relatórios e análises
- ✅ Planejamento financeiro
- ✅ Busca avançada de transações
- ✅ Perfil de usuário editável
- ✅ Sistema de suporte via chat

### Para Administradores
- ✅ Painel administrativo completo
- ✅ Gestão de usuários
- ✅ Analytics e relatórios
- ✅ Gestão de agentes de suporte
- ✅ Sistema de respostas rápidas
- ✅ Monitoramento de pagamentos

### Sistema de Planos
- 🆓 **Plano Gratuito**: Funcionalidades básicas
- 💎 **Plano Mensal**: R$ 19,00/mês
- 💎 **Plano Semestral**: R$ 89,00/semestre
- 💎 **Plano Anual**: R$ 149,00/ano

## 🧪 Testes

Execute os testes automatizados:

```bash
python test_all_functionality.py
```

## 🤝 Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

**FynanPro** - Transformando a gestão financeira pessoal 💰✨