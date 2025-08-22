# FinanProAdvanced - Formulários com Flask-WTF
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, PasswordField, EmailField, SelectField, 
                     TextAreaField, DecimalField, DateField, BooleanField,
                     SubmitField, HiddenField)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional
from wtforms.widgets import TextArea
from datetime import date
from models_advanced import AccountType, TransactionType, RecurrenceType

# Formulário de Login
class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()],
                      render_kw={'placeholder': 'seu@email.com', 'class': 'form-control'})
    password = PasswordField('Senha', validators=[DataRequired()],
                           render_kw={'placeholder': 'Sua senha', 'class': 'form-control'})
    remember_me = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar', render_kw={'class': 'btn btn-primary w-100'})

# Formulário de Registro
class RegistrationForm(FlaskForm):
    first_name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=80)],
                           render_kw={'placeholder': 'Seu nome', 'class': 'form-control'})
    last_name = StringField('Sobrenome', validators=[DataRequired(), Length(min=2, max=80)],
                          render_kw={'placeholder': 'Seu sobrenome', 'class': 'form-control'})
    email = EmailField('Email', validators=[DataRequired(), Email()],
                      render_kw={'placeholder': 'seu@email.com', 'class': 'form-control'})
    password = PasswordField('Senha', validators=[
        DataRequired(), Length(min=6, message='A senha deve ter pelo menos 6 caracteres')
    ], render_kw={'placeholder': 'Mínimo 6 caracteres', 'class': 'form-control'})
    password2 = PasswordField('Confirmar Senha', validators=[
        DataRequired(), EqualTo('password', message='As senhas devem coincidir')
    ], render_kw={'placeholder': 'Digite a senha novamente', 'class': 'form-control'})
    phone = StringField('Telefone', validators=[Optional(), Length(max=20)],
                       render_kw={'placeholder': '(11) 99999-9999', 'class': 'form-control'})
    submit = SubmitField('Criar Conta', render_kw={'class': 'btn btn-success w-100'})

# Formulário de Perfil
class ProfileForm(FlaskForm):
    first_name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=80)],
                           render_kw={'class': 'form-control'})
    last_name = StringField('Sobrenome', validators=[DataRequired(), Length(min=2, max=80)],
                          render_kw={'class': 'form-control'})
    email = EmailField('Email', validators=[DataRequired(), Email()],
                      render_kw={'class': 'form-control', 'readonly': True})
    phone = StringField('Telefone', validators=[Optional(), Length(max=20)],
                       render_kw={'class': 'form-control'})
    birth_date = DateField('Data de Nascimento', validators=[Optional()],
                          render_kw={'class': 'form-control'})
    preferred_currency = SelectField('Moeda Preferida', choices=[
        ('BRL', 'Real Brasileiro (R$)'),
        ('USD', 'Dólar Americano ($)'),
        ('EUR', 'Euro (€)')
    ], default='BRL', render_kw={'class': 'form-select'})
    profile_image = FileField('Foto do Perfil', validators=[
        Optional(), FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens!')
    ], render_kw={'class': 'form-control'})
    submit = SubmitField('Salvar Alterações', render_kw={'class': 'btn btn-primary'})

# Formulário de Conta Bancária
class AccountForm(FlaskForm):
    name = StringField('Nome da Conta', validators=[DataRequired(), Length(min=2, max=100)],
                      render_kw={'placeholder': 'Ex: Conta Corrente Banco do Brasil', 'class': 'form-control'})
    account_type = SelectField('Tipo de Conta', choices=[
        (AccountType.CORRENTE.value, 'Conta Corrente'),
        (AccountType.POUPANCA.value, 'Poupança'),
        (AccountType.CARTAO_CREDITO.value, 'Cartão de Crédito'),
        (AccountType.INVESTIMENTO.value, 'Investimento'),
        (AccountType.DINHEIRO.value, 'Dinheiro')
    ], validators=[DataRequired()], render_kw={'class': 'form-select'})
    bank_name = StringField('Nome do Banco', validators=[Optional(), Length(max=100)],
                           render_kw={'placeholder': 'Ex: Banco do Brasil', 'class': 'form-control'})
    bank_code = StringField('Código do Banco', validators=[Optional(), Length(max=10)],
                           render_kw={'placeholder': 'Ex: 001', 'class': 'form-control'})
    agency = StringField('Agência', validators=[Optional(), Length(max=20)],
                        render_kw={'placeholder': 'Ex: 1234-5', 'class': 'form-control'})
    account_number = StringField('Número da Conta', validators=[Optional(), Length(max=50)],
                                render_kw={'placeholder': 'Ex: 12345-6', 'class': 'form-control'})
    initial_balance = DecimalField('Saldo Inicial', validators=[DataRequired()], default=0.00,
                                  render_kw={'step': '0.01', 'class': 'form-control'})
    credit_limit = DecimalField('Limite de Crédito', validators=[Optional()], default=0.00,
                               render_kw={'step': '0.01', 'class': 'form-control'})
    color = StringField('Cor', validators=[Optional()], default='#007bff',
                       render_kw={'type': 'color', 'class': 'form-control'})
    is_active = BooleanField('Conta Ativa', default=True)
    include_in_total = BooleanField('Incluir no Total Geral', default=True)
    submit = SubmitField('Salvar Conta', render_kw={'class': 'btn btn-primary'})

# Formulário de Transação
class TransactionForm(FlaskForm):
    description = StringField('Descrição', validators=[DataRequired(), Length(min=2, max=200)],
                            render_kw={'placeholder': 'Ex: Pagamento conta de luz', 'class': 'form-control'})
    amount = DecimalField('Valor', validators=[DataRequired(), NumberRange(min=0.01)],
                         render_kw={'step': '0.01', 'placeholder': '0,00', 'class': 'form-control'})
    date = DateField('Data', validators=[DataRequired()], default=date.today,
                    render_kw={'class': 'form-control'})
    transaction_type = SelectField('Tipo', choices=[
        (TransactionType.RECEITA.value, 'Receita'),
        (TransactionType.DESPESA.value, 'Despesa'),
        (TransactionType.TRANSFERENCIA.value, 'Transferência')
    ], validators=[DataRequired()], render_kw={'class': 'form-select'})
    account_id = SelectField('Conta', coerce=int, validators=[DataRequired()],
                           render_kw={'class': 'form-select'})
    chart_account_id = SelectField('Categoria', coerce=int, validators=[DataRequired()],
                                 render_kw={'class': 'form-select'})
    transfer_account_id = SelectField('Conta Destino', coerce=int, validators=[Optional()],
                                    render_kw={'class': 'form-select'})
    notes = TextAreaField('Observações', validators=[Optional()],
                         render_kw={'rows': 3, 'placeholder': 'Observações adicionais...', 'class': 'form-control'})
    reference = StringField('Referência/Documento', validators=[Optional(), Length(max=100)],
                           render_kw={'placeholder': 'Número do documento, nota fiscal, etc.', 'class': 'form-control'})
    tags = StringField('Tags', validators=[Optional(), Length(max=500)],
                      render_kw={'placeholder': 'casa, mercado, combustível (separar por vírgula)', 'class': 'form-control'})
    recurrence_type = SelectField('Recorrência', choices=[
        (RecurrenceType.UNICA.value, 'Única'),
        (RecurrenceType.DIARIA.value, 'Diária'),
        (RecurrenceType.SEMANAL.value, 'Semanal'),
        (RecurrenceType.QUINZENAL.value, 'Quinzenal'),
        (RecurrenceType.MENSAL.value, 'Mensal'),
        (RecurrenceType.BIMESTRAL.value, 'Bimestral'),
        (RecurrenceType.TRIMESTRAL.value, 'Trimestral'),
        (RecurrenceType.SEMESTRAL.value, 'Semestral'),
        (RecurrenceType.ANUAL.value, 'Anual')
    ], default=RecurrenceType.UNICA.value, render_kw={'class': 'form-select'})
    recurrence_end_date = DateField('Fim da Recorrência', validators=[Optional()],
                                   render_kw={'class': 'form-control'})
    attachment = FileField('Anexo', validators=[
        Optional(), FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Apenas PDF e imagens!')
    ], render_kw={'class': 'form-control'})
    is_confirmed = BooleanField('Confirmada', default=True)
    submit = SubmitField('Salvar Transação', render_kw={'class': 'btn btn-primary'})

# Formulário de Plano de Contas
class ChartOfAccountsForm(FlaskForm):
    code = StringField('Código', validators=[DataRequired(), Length(min=1, max=20)],
                      render_kw={'placeholder': 'Ex: 1.1.01', 'class': 'form-control'})
    name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=200)],
                      render_kw={'placeholder': 'Ex: Salário', 'class': 'form-control'})
    description = TextAreaField('Descrição', validators=[Optional()],
                               render_kw={'rows': 3, 'placeholder': 'Descrição detalhada da conta...', 'class': 'form-control'})
    parent_id = SelectField('Conta Pai', coerce=int, validators=[Optional()],
                          render_kw={'class': 'form-select'})
    account_type = SelectField('Tipo', choices=[
        (TransactionType.RECEITA.value, 'Receita'),
        (TransactionType.DESPESA.value, 'Despesa')
    ], validators=[DataRequired()], render_kw={'class': 'form-select'})
    is_summary = BooleanField('Conta Sintética (não aceita lançamentos)')
    is_active = BooleanField('Ativa', default=True)
    submit = SubmitField('Salvar Conta', render_kw={'class': 'btn btn-primary'})

# Formulário de Orçamento
class BudgetForm(FlaskForm):
    name = StringField('Nome do Orçamento', validators=[DataRequired(), Length(min=2, max=100)],
                      render_kw={'placeholder': 'Ex: Orçamento Janeiro 2024', 'class': 'form-control'})
    description = TextAreaField('Descrição', validators=[Optional()],
                               render_kw={'rows': 3, 'placeholder': 'Descrição do orçamento...', 'class': 'form-control'})
    start_date = DateField('Data Início', validators=[DataRequired()],
                          render_kw={'class': 'form-control'})
    end_date = DateField('Data Fim', validators=[DataRequired()],
                        render_kw={'class': 'form-control'})
    planned_income = DecimalField('Receita Planejada', validators=[DataRequired()], default=0.00,
                                 render_kw={'step': '0.01', 'class': 'form-control'})
    planned_expenses = DecimalField('Despesa Planejada', validators=[DataRequired()], default=0.00,
                                   render_kw={'step': '0.01', 'class': 'form-control'})
    is_active = BooleanField('Ativo', default=True)
    auto_create_next = BooleanField('Criar automaticamente o próximo período')
    submit = SubmitField('Salvar Orçamento', render_kw={'class': 'btn btn-primary'})

# Formulário de Item do Orçamento
class BudgetItemForm(FlaskForm):
    chart_account_id = SelectField('Conta/Categoria', coerce=int, validators=[DataRequired()],
                                 render_kw={'class': 'form-select'})
    planned_amount = DecimalField('Valor Planejado', validators=[DataRequired(), NumberRange(min=0.01)],
                                 render_kw={'step': '0.01', 'class': 'form-control'})
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Adicionar Item', render_kw={'class': 'btn btn-primary'})

# Formulário de Perfil Familiar
class FamilyProfileForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(), Length(min=2, max=100)],
                      render_kw={'placeholder': 'Nome do familiar', 'class': 'form-control'})
    relationship = StringField('Parentesco', validators=[Optional(), Length(max=50)],
                              render_kw={'placeholder': 'Ex: Cônjuge, Filho(a), Pai, Mãe', 'class': 'form-control'})
    birth_date = DateField('Data de Nascimento', validators=[Optional()],
                          render_kw={'class': 'form-control'})
    is_active = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar Perfil', render_kw={'class': 'btn btn-primary'})

# Formulário de Busca
class SearchForm(FlaskForm):
    search_query = StringField('Buscar', validators=[DataRequired(), Length(min=1, max=200)],
                              render_kw={'placeholder': 'Digite sua busca...', 'class': 'form-control'})
    search_type = SelectField('Buscar em', choices=[
        ('transactions', 'Transações'),
        ('accounts', 'Contas'),
        ('categories', 'Categorias')
    ], default='transactions', render_kw={'class': 'form-select'})
    submit = SubmitField('Buscar', render_kw={'class': 'btn btn-outline-primary'})

# Formulário de Filtros
class FilterForm(FlaskForm):
    start_date = DateField('Data Início', validators=[Optional()],
                          render_kw={'class': 'form-control'})
    end_date = DateField('Data Fim', validators=[Optional()],
                        render_kw={'class': 'form-control'})
    account_id = SelectField('Conta', coerce=int, validators=[Optional()],
                           render_kw={'class': 'form-select'})
    chart_account_id = SelectField('Categoria', coerce=int, validators=[Optional()],
                                 render_kw={'class': 'form-select'})
    transaction_type = SelectField('Tipo', choices=[
        ('', 'Todos'),
        (TransactionType.RECEITA.value, 'Receitas'),
        (TransactionType.DESPESA.value, 'Despesas'),
        (TransactionType.TRANSFERENCIA.value, 'Transferências')
    ], default='', render_kw={'class': 'form-select'})
    min_amount = DecimalField('Valor Mínimo', validators=[Optional()],
                             render_kw={'step': '0.01', 'class': 'form-control'})
    max_amount = DecimalField('Valor Máximo', validators=[Optional()],
                             render_kw={'step': '0.01', 'class': 'form-control'})
    submit = SubmitField('Filtrar', render_kw={'class': 'btn btn-outline-primary'})

# Formulário de Importação CSV
class ImportCSVForm(FlaskForm):
    csv_file = FileField('Arquivo CSV', validators=[
        DataRequired(), FileAllowed(['csv'], 'Apenas arquivos CSV!')
    ], render_kw={'class': 'form-control'})
    account_id = SelectField('Conta de Destino', coerce=int, validators=[DataRequired()],
                           render_kw={'class': 'form-select'})
    date_format = SelectField('Formato de Data', choices=[
        ('%d/%m/%Y', 'DD/MM/AAAA'),
        ('%Y-%m-%d', 'AAAA-MM-DD'),
        ('%m/%d/%Y', 'MM/DD/AAAA')
    ], default='%d/%m/%Y', render_kw={'class': 'form-select'})
    decimal_separator = SelectField('Separador Decimal', choices=[
        (',', 'Vírgula (1.234,56)'),
        ('.', 'Ponto (1,234.56)')
    ], default=',', render_kw={'class': 'form-select'})
    has_header = BooleanField('Arquivo possui cabeçalho', default=True)
    submit = SubmitField('Importar', render_kw={'class': 'btn btn-success'})
