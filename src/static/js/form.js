// Cupido - Form validation & submission

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('message-form');
    const token = document.getElementById('form-token').value;
    const maxMessages = parseInt(document.getElementById('max-messages')?.value || '1');
    const isPremium = document.getElementById('is-premium')?.value === 'true';

    if (isPremium) return; // Premium uses its own JS

    // Phone mask
    const phoneInput = document.getElementById('recipient_phone');
    if (phoneInput) {
        phoneInput.addEventListener('input', (e) => {
            let v = e.target.value.replace(/\D/g, '');
            if (v.length > 11) v = v.slice(0, 11);
            if (v.length > 7) {
                v = `(${v.slice(0,2)}) ${v.slice(2,7)}-${v.slice(7)}`;
            } else if (v.length > 2) {
                v = `(${v.slice(0,2)}) ${v.slice(2)}`;
            }
            e.target.value = v;
        });
    }

    // Character counter
    const messageInput = document.getElementById('message');
    const charCount = document.getElementById('char-count');
    if (messageInput && charCount) {
        messageInput.addEventListener('input', () => {
            charCount.textContent = messageInput.value.length;
        });
    }

    // Extra messages (multi plan)
    let extraCount = 0;
    const addBtn = document.getElementById('add-message-btn');
    const extraFields = document.getElementById('extra-fields');

    if (addBtn && extraFields) {
        addBtn.addEventListener('click', () => {
            if (extraCount >= maxMessages - 1) {
                addBtn.disabled = true;
                return;
            }
            extraCount++;
            const div = document.createElement('div');
            div.className = 'form-group';
            div.innerHTML = `
                <label>Mensagem ${extraCount + 1}</label>
                <textarea class="extra-message" rows="3"
                          placeholder="Mensagem adicional..."
                          maxlength="1000"></textarea>
            `;
            extraFields.appendChild(div);
            if (extraCount >= maxMessages - 1) addBtn.disabled = true;
        });
    }

    // Form submit
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = document.getElementById('submit-btn');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Enviando...';

            const phone = phoneInput.value.replace(/\D/g, '');
            const message = messageInput.value.trim();
            const nickname = document.getElementById('sender_nickname').value.trim();

            if (phone.length < 10) {
                showToast('Telefone invalido', true);
                submitBtn.disabled = false;
                submitBtn.textContent = '💘 Enviar Mensagem';
                return;
            }

            if (!message) {
                showToast('Escreva sua mensagem', true);
                submitBtn.disabled = false;
                submitBtn.textContent = '💘 Enviar Mensagem';
                return;
            }

            // Collect extra messages
            const extraMessages = [];
            document.querySelectorAll('.extra-message').forEach(el => {
                if (el.value.trim()) extraMessages.push(el.value.trim());
            });

            try {
                const resp = await fetch(`/form/${token}/submit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        recipient_phone: phone,
                        message: message,
                        sender_nickname: nickname || 'Alguem especial',
                        extra_messages: extraMessages,
                    }),
                });

                const data = await resp.json();

                if (resp.ok) {
                    // Replace page with success
                    document.querySelector('.container').innerHTML = `
                        <div class="card success-card">
                            <div class="card-header">
                                <div class="logo">💌</div>
                                <h1>Mensagem Enviada!</h1>
                                <p class="subtitle">O Cupido ja entregou sua mensagem</p>
                            </div>
                            <div class="success-body">
                                <p>A pessoa especial ja recebeu no WhatsApp!</p>
                                <p class="hint">Agora e so esperar... 💘</p>
                            </div>
                        </div>
                    `;
                } else {
                    showToast(data.error || 'Erro ao enviar', true);
                    submitBtn.disabled = false;
                    submitBtn.textContent = '💘 Enviar Mensagem';
                }
            } catch (err) {
                showToast('Erro de conexao', true);
                submitBtn.disabled = false;
                submitBtn.textContent = '💘 Enviar Mensagem';
            }
        });
    }
});

function showToast(msg, isError = false) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast ${isError ? 'error' : ''} show`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
