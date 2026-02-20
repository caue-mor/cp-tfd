// Stitch Cupido Quiz v2 — Narrative + Video + Pricing

class StitchCupido {
    constructor() {
        this.currentQuestion = 1;
        this.totalQuestions = 4;
        this.answers = {};
        this.progressBar = document.getElementById('progressFill');

        // Narrativas por seleção
        this.narratives = {
            // Q1 - Situação
            solteiro: '💔 Entendi... você tá na fase de querer conquistar alguém! O Stitch vai te ajudar a dar o primeiro passo de um jeito inesquecível.',
            relacionamento: '💕 Que lindo! Surpreender quem já está com você é ainda mais especial. Vamos criar algo único!',
            complicado: '😔 Eu sei como é... às vezes as palavras certas podem mudar tudo. Vamos encontrar o jeito perfeito de se expressar.',
            amizade: '🤝 Ah, a famosa friendzone... o Stitch sabe como quebrar essa barreira! Bora criar uma mensagem que muda o jogo.',

            // Q4 - Objetivo
            conquistar: '💘 Perfeito! Uma declaração anônima com a voz do Stitch? Ela não vai esquecer nunca!',
            reconquistar: '🔄 Reconquistar alguém exige coragem. Uma mensagem com o Stitch pode ser exatamente o empurrão que faltava.',
            pedir_desculpas: '🙏 Pedir desculpas é difícil, mas com as palavras certas tudo muda. O Stitch vai entregar com carinho.',
            surpreender: '🎉 Todo mundo merece uma surpresa! O Stitch vai fazer essa pessoa rir e se emocionar ao mesmo tempo.',
        };

        this.initializeEventListeners();
        this.createParticles();
    }

    // ── Narrativas ────────────────────────────────────────

    updateNarrative(key) {
        const text = this.narratives[key];
        if (!text) return;

        const bubble = document.getElementById('narrativeBubble');
        const textEl = document.getElementById('narrativeText');

        bubble.style.opacity = '0';
        bubble.style.transform = 'translateY(10px)';

        setTimeout(() => {
            textEl.textContent = text;
            bubble.style.opacity = '1';
            bubble.style.transform = 'translateY(0)';
        }, 300);
    }

    narrativeForName(name) {
        const bubble = document.getElementById('narrativeBubble');
        const textEl = document.getElementById('narrativeText');

        bubble.style.opacity = '0';
        setTimeout(() => {
            textEl.textContent = '✨ Prazer, ' + name + '! Agora preciso do seu WhatsApp pra te mandar os detalhes por lá.';
            bubble.style.opacity = '1';
        }, 300);
    }

    narrativeForPhone() {
        const bubble = document.getElementById('narrativeBubble');
        const textEl = document.getElementById('narrativeText');

        bubble.style.opacity = '0';
        setTimeout(() => {
            textEl.textContent = '📱 Ótimo! Agora me conta: qual é o seu objetivo com essa mensagem?';
            bubble.style.opacity = '1';
        }, 300);
    }

    // ── Validação ─────────────────────────────────────────

    validateName(name) {
        return name && name.trim().length >= 2 && name.trim().length <= 50;
    }

    validatePhone(phone) {
        const clean = phone.replace(/\D/g, '');
        return clean.length >= 10 && clean.length <= 11;
    }

    formatPhone(phone) {
        const c = phone.replace(/\D/g, '');
        if (c.length === 11) return c.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
        if (c.length === 10) return c.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
        return phone;
    }

    // ── Event Listeners ───────────────────────────────────

    initializeEventListeners() {
        // Botões de opção
        document.querySelectorAll('.option-button').forEach(btn => {
            btn.addEventListener('click', (e) => this.selectOption(e.target.closest('.option-button')));
        });

        // Input de nome
        const nameInput = document.getElementById('userName');
        if (nameInput) {
            nameInput.addEventListener('input', (e) => this.validateInputField(e.target, 'name'));
        }

        // Input de telefone
        const phoneInput = document.getElementById('userPhone');
        if (phoneInput) {
            phoneInput.addEventListener('input', (e) => {
                e.target.value = this.formatPhone(e.target.value);
                this.validateInputField(e.target, 'phone');
            });
        }

        // Botões de próxima
        for (let i = 1; i <= this.totalQuestions; i++) {
            const btn = document.getElementById('nextBtn' + i);
            if (btn) {
                btn.addEventListener('click', () => {
                    if (i === this.totalQuestions) {
                        this.showVideoSection();
                    } else {
                        this.nextQuestion();
                    }
                });
            }
        }

        // Continuar do vídeo para resultados
        const btnVideo = document.getElementById('btnContinueVideo');
        if (btnVideo) {
            btnVideo.addEventListener('click', () => this.finishQuiz());
        }

        // Botões de CTA dos planos
        document.querySelectorAll('.price-cta').forEach(btn => {
            btn.addEventListener('click', () => {
                const note = document.querySelector('.pricing-whatsapp-note');
                if (note) {
                    note.style.background = 'rgba(34,197,94,0.25)';
                    note.style.borderColor = 'rgba(34,197,94,0.5)';
                    note.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            });
        });
    }

    // ── Validação de Input ────────────────────────────────

    validateInputField(input, type) {
        const value = input.value.trim();
        const isValid = type === 'name' ? this.validateName(value) : this.validatePhone(value);

        input.classList.remove('valid', 'invalid');
        if (value.length > 0) input.classList.add(isValid ? 'valid' : 'invalid');

        const qNum = input.closest('.question-card').dataset.question;
        const nextBtn = document.getElementById('nextBtn' + qNum);

        if (isValid) {
            nextBtn.classList.add('enabled');
            this.answers['q' + qNum] = value;
        } else {
            nextBtn.classList.remove('enabled');
            delete this.answers['q' + qNum];
        }
    }

    // ── Seleção de Opção ──────────────────────────────────

    selectOption(selectedButton) {
        const card = selectedButton.closest('.question-card');
        const qNum = card.dataset.question;
        const value = selectedButton.dataset.value;

        card.querySelectorAll('.option-button').forEach(b => b.classList.remove('selected'));
        selectedButton.classList.add('selected');

        this.answers['q' + qNum] = value;
        document.getElementById('nextBtn' + qNum).classList.add('enabled');

        // Atualizar narrativa
        this.updateNarrative(value);
    }

    // ── Navegação ─────────────────────────────────────────

    nextQuestion() {
        const currentCard = document.querySelector('[data-question="' + this.currentQuestion + '"]');
        currentCard.classList.remove('active');

        // Narrativa para transição de nome/telefone
        if (this.currentQuestion === 2 && this.answers.q2) {
            this.narrativeForName(this.answers.q2);
        }
        if (this.currentQuestion === 3) {
            this.narrativeForPhone();
        }

        this.currentQuestion++;

        const nextCard = document.querySelector('[data-question="' + this.currentQuestion + '"]');
        if (nextCard) {
            nextCard.classList.add('active');
            this.progressBar.style.width = (this.currentQuestion / this.totalQuestions * 100) + '%';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }

    // ── Seção do Vídeo ────────────────────────────────────

    showVideoSection() {
        document.querySelector('[data-question="' + this.currentQuestion + '"]').classList.remove('active');
        this.progressBar.style.width = '100%';

        // Esconder narrativa durante o vídeo
        document.getElementById('narrativeBubble').style.display = 'none';

        document.getElementById('videoSection').classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // ── Finalizar Quiz ────────────────────────────────────

    async finishQuiz() {
        // Esconder vídeo
        document.getElementById('videoSection').classList.remove('active');

        // Analisar e mostrar resultado
        const result = this.analyzeAnswers();
        this.showResult(result);

        // Enviar contato para o backend
        await this.sendContactToBackend();

        // Mostrar planos após breve delay
        setTimeout(() => {
            document.getElementById('pricingSection').classList.add('active');
            setTimeout(() => {
                document.getElementById('pricingSection').scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 400);
        }, 2000);
    }

    // ── Análise ───────────────────────────────────────────

    analyzeAnswers() {
        const situacao = this.answers.q1;
        const objetivo = this.answers.q4;
        const nome = this.answers.q2 || '';

        if (objetivo === 'pedir_desculpas' || situacao === 'complicado') {
            return {
                emoji: '🙏',
                title: 'Pedido de Desculpas',
                subtitle: nome
                    ? nome + ', o Stitch vai entregar suas palavras com todo carinho. Às vezes tudo que a pessoa precisa é ouvir um "desculpa" de verdade.'
                    : 'O Stitch vai entregar suas palavras com todo carinho.'
            };
        }
        if (objetivo === 'reconquistar') {
            return {
                emoji: '💔',
                title: 'Reconquista do Amor',
                subtitle: nome
                    ? nome + ', uma mensagem surpresa com a voz do Stitch pode ser o primeiro passo pra reconectar. Coragem!'
                    : 'Uma mensagem surpresa pode ser o primeiro passo pra reconectar.'
            };
        }
        if (situacao === 'solteiro' || objetivo === 'conquistar') {
            return {
                emoji: '💘',
                title: 'Declaração de Amor',
                subtitle: nome
                    ? nome + ', imagina a cara dela recebendo uma mensagem anônima com a voz do Stitch? Vai ser inesquecível!'
                    : 'Imagina a reação ao receber uma mensagem anônima com a voz do Stitch!'
            };
        }
        if (objetivo === 'surpreender') {
            return {
                emoji: '🎉',
                title: 'Surpresa Especial',
                subtitle: nome
                    ? nome + ', surpresa + Stitch = combinação perfeita! Ela vai morrer de rir e se emocionar ao mesmo tempo.'
                    : 'Surpresa + Stitch = combinação perfeita!'
            };
        }
        return {
            emoji: '❤️',
            title: 'Mensagem do Coração',
            subtitle: nome
                ? nome + ', sua mensagem vai tocar o coração dessa pessoa de um jeito único!'
                : 'Sua mensagem vai tocar o coração dessa pessoa!'
        };
    }

    showResult(result) {
        const resultCard = document.getElementById('resultCard');
        document.getElementById('resultEmoji').textContent = result.emoji;
        document.getElementById('resultTitle').textContent = result.title;
        document.getElementById('resultSubtitle').textContent = result.subtitle;

        resultCard.classList.add('active');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // ── API Backend ───────────────────────────────────────

    async sendContactToBackend() {
        const nome = this.answers.q2 || '';
        const telefone = this.answers.q3 || '';

        if (!nome || !telefone) return;

        try {
            const response = await fetch('/api/quiz/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nome: nome,
                    telefone: telefone,
                    situacao: this.answers.q1 || '',
                    objetivo: this.answers.q4 || '',
                }),
            });

            const data = await response.json();
            if (data.success) {
                console.log('Contato enviado com sucesso!');
            } else {
                console.error('Erro ao enviar contato:', data);
            }
        } catch (err) {
            console.error('Erro de conexão:', err);
        }
    }

    // ── Partículas ────────────────────────────────────────

    createParticles() {
        const container = document.getElementById('particles');
        setInterval(() => {
            const p = document.createElement('div');
            p.classList.add('particle');
            const size = Math.random() * 6 + 2;
            p.style.width = size + 'px';
            p.style.height = size + 'px';
            p.style.left = (Math.random() * 100) + 'vw';
            const dur = Math.random() * 3 + 5;
            p.style.animationDuration = dur + 's';
            container.appendChild(p);
            setTimeout(() => p.remove(), dur * 1000);
        }, 600);
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    window.stitchInstance = new StitchCupido();
});
