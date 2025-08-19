// Chat Widget JavaScript
class ChatWidget {
    constructor() {
        this.isOpen = false;
        this.hasNewMessage = false;
        this.init();
    }

    init() {
        this.createWidget();
        this.bindEvents();
        
        // Simular nova mensagem após 10 segundos
        setTimeout(() => {
            this.showNotification();
        }, 10000);
    }

    createWidget() {
        const widgetHTML = `
            <div class="chat-widget">
                <button class="chat-toggle" id="chatToggle" title="Abrir chat de suporte">
                    <i class="fas fa-comments"></i>
                    <div class="chat-notification" id="chatNotification" style="display: none;">1</div>
                </button>
                
                <div class="chat-popup" id="chatPopup">
                    <div class="chat-popup-header">
                        <h6>💬 Suporte Finance SaaS</h6>
                        <button class="chat-popup-close" id="chatClose" title="Fechar chat">×</button>
                    </div>
                    
                    <div class="chat-popup-messages" id="chatPopupMessages">
                        <div class="message bot mb-3">
                            <div class="alert alert-info mb-0">
                                <strong>Olá! 👋</strong><br>
                                Como posso ajudar? Selecione uma opção:
                            </div>
                        </div>
                        
                        <!-- Botões de ajuda rápida -->
                        <div class="mb-3">
                            <div class="btn-group-vertical w-100" role="group">
                                <button class="btn btn-outline-primary btn-sm quick-help" data-message="Como adicionar transação?">
                                    <i class="fas fa-plus-circle me-2"></i>Adicionar Transação
                                </button>
                                <button class="btn btn-outline-primary btn-sm quick-help" data-message="Como organizar categorias?">
                                    <i class="fas fa-tags me-2"></i>Gerenciar Categorias
                                </button>
                                <button class="btn btn-outline-primary btn-sm quick-help" data-message="Como ver meus relatórios?">
                                    <i class="fas fa-chart-bar me-2"></i>Relatórios
                                </button>
                                <button class="btn btn-outline-success btn-sm quick-help" data-message="Problemas técnicos">
                                    <i class="fas fa-tools me-2"></i>Problemas Técnicos
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chat-popup-input">
                        <div class="input-group input-group-sm">
                            <input type="text" class="form-control" id="chatQuickInput" 
                                   placeholder="Digite sua mensagem..." maxlength="200">
                            <button class="btn btn-primary" id="chatQuickSend" title="Enviar mensagem">
                                <i class="fas fa-paper-plane"></i>
                            </button>
                        </div>
                        <div class="text-center mt-2">
                            <a href="/support" class="btn btn-outline-primary btn-sm">
                                <i class="fas fa-expand me-1"></i>Chat Completo
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', widgetHTML);
    }

    bindEvents() {
        const toggle = document.getElementById('chatToggle');
        const popup = document.getElementById('chatPopup');
        const close = document.getElementById('chatClose');
        const send = document.getElementById('chatQuickSend');
        const input = document.getElementById('chatQuickInput');

        toggle.addEventListener('click', () => this.toggleChat());
        close.addEventListener('click', () => this.closeChat());
        send.addEventListener('click', () => this.sendQuickMessage());
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendQuickMessage();
            }
        });

        // Event listeners para botões de ajuda rápida
        document.addEventListener('click', (e) => {
            if (e.target.closest('.quick-help')) {
                const button = e.target.closest('.quick-help');
                const message = button.dataset.message;
                this.sendQuickMessage(message);
            }
        });

        // Fechar ao clicar fora
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.chat-widget') && this.isOpen) {
                this.closeChat();
            }
        });
    }

    toggleChat() {
        const popup = document.getElementById('chatPopup');
        
        if (this.isOpen) {
            this.closeChat();
        } else {
            popup.style.display = 'block';
            this.isOpen = true;
            this.hideNotification();
            
            // Focus no input
            setTimeout(() => {
                document.getElementById('chatQuickInput').focus();
            }, 100);
        }
    }

    closeChat() {
        const popup = document.getElementById('chatPopup');
        popup.style.display = 'none';
        this.isOpen = false;
    }

    sendQuickMessage(predefinedMessage = null) {
        const input = document.getElementById('chatQuickInput');
        const message = predefinedMessage || input.value.trim();
        
        if (!message) return;

        // Adicionar mensagem do usuário
        this.addMessage('user', message);
        
        // Limpar input apenas se não foi mensagem predefinida
        if (!predefinedMessage) {
            input.value = '';
        }

        // Simular resposta automática
        setTimeout(() => {
            const autoResponse = this.getAutoResponse(message);
            this.addMessage('bot', autoResponse);
        }, 1000);
    }

    addMessage(sender, text) {
        const messagesContainer = document.getElementById('chatPopupMessages');
        const messageClass = sender === 'user' ? 'alert-primary' : 'alert-info';
        const messageHTML = `
            <div class="message ${sender} mb-2">
                <div class="alert ${messageClass} mb-0 py-2 px-3">
                    ${sender === 'bot' ? '<strong>Suporte:</strong><br>' : ''}${text}
                </div>
            </div>
        `;
        
        messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    getAutoResponse(message) {
        const lowercaseMessage = message.toLowerCase();
        
        // Respostas sobre funcionalidades
        if (lowercaseMessage.includes('transação') || lowercaseMessage.includes('lançamento') || lowercaseMessage.includes('adicionar')) {
            return 'Para adicionar transação: 1) Menu "Nova Transação" 2) Preencha descrição e valor 3) Escolha receita/despesa 4) Selecione categoria 5) Salvar! 💰';
        }
        
        if (lowercaseMessage.includes('categoria') || lowercaseMessage.includes('organizar')) {
            return 'As categorias organizam seus gastos! Acesse "Categorias" no menu para criar novas ou editar. Temos categorias como Alimentação, Transporte, etc. 🏷️';
        }
        
        if (lowercaseMessage.includes('relatório') || lowercaseMessage.includes('gráfico') || lowercaseMessage.includes('indicador')) {
            return 'Seus relatórios estão em "Indicadores" e "Saúde Financeira". Veja gráficos por categoria, evolução mensal e dicas personalizadas! 📈';
        }
        
        if (lowercaseMessage.includes('saldo') || lowercaseMessage.includes('balanço')) {
            return 'Seu saldo é calculado: Receitas - Despesas = Saldo atual. Veja no Dashboard ou Indicadores para análise detalhada! 💰';
        }
        
        if (lowercaseMessage.includes('receita') || lowercaseMessage.includes('ganho')) {
            return 'Para lançar receita: Nova Transação → Receita → Digite valor e descrição → Categoria (Salário, Freelance...) → Salvar! 💚';
        }
        
        if (lowercaseMessage.includes('despesa') || lowercaseMessage.includes('gasto')) {
            return 'Para lançar despesa: Nova Transação → Despesa → Digite valor e descrição → Categoria (Alimentação, Transporte...) → Salvar! ❌';
        }
        
        // Respostas sobre problemas técnicos
        if (lowercaseMessage.includes('erro') || lowercaseMessage.includes('problema') || lowercaseMessage.includes('bug')) {
            return 'Problemas técnicos? 1) Atualize a página (F5) 2) Limpe cache 3) Tente outro navegador. Se persistir, nos contate! 🔧';
        }
        
        if (lowercaseMessage.includes('lento') || lowercaseMessage.includes('travando')) {
            return 'Sistema lento? Verifique sua conexão, feche outras abas e limpe cache. Nossos servidores estão otimizados! ⚡';
        }
        
        if (lowercaseMessage.includes('login') || lowercaseMessage.includes('senha') || lowercaseMessage.includes('entrar')) {
            return 'Problemas de login? Verifique email/senha, tente recuperar senha ou limpe cookies. Precisa de ajuda específica? 🔐';
        }
        
        // Respostas sobre planos
        if (lowercaseMessage.includes('plano') || lowercaseMessage.includes('preço')) {
            return 'Temos planos a partir de R$ 9,90/mês! Acesse "Planos" no menu para ver todas as opções. 😊';
        }
        
        if (lowercaseMessage.includes('gratuito') || lowercaseMessage.includes('free')) {
            return 'Plano gratuito inclui: 50 transações/mês, categorias básicas e relatórios simples. Planos pagos são ilimitados! 🆓';
        }
        
        if (lowercaseMessage.includes('premium') || lowercaseMessage.includes('pago')) {
            return 'Recursos premium: transações ilimitadas, categorias personalizadas, relatórios avançados, metas financeiras e backup! ⭐';
        }
        
        // Respostas sobre pagamentos
        if (lowercaseMessage.includes('pagamento') || lowercaseMessage.includes('cartão') || lowercaseMessage.includes('pix')) {
            return 'Aceitamos cartão de crédito e PIX. Todos os pagamentos são seguros via Stripe. Precisa de ajuda com algum pagamento?';
        }
        
        if (lowercaseMessage.includes('teste') || lowercaseMessage.includes('trial')) {
            return 'Você tem 7 dias grátis para testar todas as funcionalidades premium! Quer começar agora?';
        }
        
        if (lowercaseMessage.includes('cancelar')) {
            return 'Para cancelar: acesse seu perfil → "Gerenciar Plano". Você pode cancelar a qualquer momento sem multas.';
        }
        
        // Respostas sobre segurança
        if (lowercaseMessage.includes('segurança') || lowercaseMessage.includes('dados') || lowercaseMessage.includes('privacidade')) {
            return 'Seus dados são seguros! Usamos criptografia SSL, senhas protegidas e servidores seguros. Conformidade com LGPD! 🔒';
        }
        
        // Saudações
        if (lowercaseMessage.includes('oi') || lowercaseMessage.includes('olá') || lowercaseMessage.includes('help')) {
            return 'Olá! Como posso ajudá-lo hoje? Use os botões acima para dúvidas rápidas ou digite sua pergunta! 👋';
        }
        
        // Resposta padrão
        return 'Obrigada pela mensagem! Para ajuda específica, use os botões acima ou clique em "Chat Completo" para atendimento detalhado! 📧';
    }

    showNotification() {
        const notification = document.getElementById('chatNotification');
        notification.style.display = 'flex';
        this.hasNewMessage = true;
        
        // Simular mensagem
        setTimeout(() => {
            if (!this.isOpen) {
                this.addMessage('bot', 'Olá! Posso ajudá-lo com alguma dúvida sobre nossos planos? 😊');
            }
        }, 500);
    }

    hideNotification() {
        const notification = document.getElementById('chatNotification');
        notification.style.display = 'none';
        this.hasNewMessage = false;
    }
}

// Inicializar widget quando página carregar
document.addEventListener('DOMContentLoaded', function() {
    // Só criar o widget se não estivermos na página de suporte
    if (!window.location.pathname.includes('/support')) {
        new ChatWidget();
    }
});
