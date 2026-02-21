// Cupido - Form validation & submission (multi-message + audio + scheduling)

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('message-form');
    const token = document.getElementById('form-token').value;
    const maxMessages = parseInt(document.getElementById('max-messages')?.value || '1');
    const messagesSent = parseInt(document.getElementById('messages-sent')?.value || '0');
    const remaining = parseInt(document.getElementById('remaining')?.value || '1');
    const hasAudio = document.getElementById('has-audio')?.value === 'true';
    const audioCharLimit = parseInt(document.getElementById('audio-char-limit')?.value || '0');
    const isPremium = document.getElementById('is-premium')?.value === 'true';

    if (isPremium) return; // Premium uses its own JS

    // Phone mask
    const phoneInput = document.getElementById('recipient_phone');
    if (phoneInput && !phoneInput.readOnly) {
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

    // Message character counter
    const messageInput = document.getElementById('message');
    const charCount = document.getElementById('char-count');
    if (messageInput && charCount) {
        messageInput.addEventListener('input', () => {
            charCount.textContent = messageInput.value.length;
        });
    }

    // Audio text character counter
    const audioTextInput = document.getElementById('audio_text');
    const audioCharCount = document.getElementById('audio-char-count');
    if (audioTextInput && audioCharCount) {
        audioTextInput.addEventListener('input', () => {
            const len = audioTextInput.value.length;
            audioCharCount.textContent = len;
            // Visual feedback when approaching limit
            const parent = audioCharCount.closest('.char-count');
            if (parent) {
                parent.classList.toggle('near-limit', len > audioCharLimit * 0.8);
                parent.classList.toggle('at-limit', len >= audioCharLimit);
            }
        });
    }

    // Schedule toggle
    const scheduleToggle = document.getElementById('schedule-toggle');
    const schedulePicker = document.getElementById('schedule-picker');
    const scheduledAtInput = document.getElementById('scheduled_at');

    if (scheduleToggle && schedulePicker && scheduledAtInput) {
        // Set min datetime to now + 5 minutes
        const setMinDatetime = () => {
            const now = new Date();
            now.setMinutes(now.getMinutes() + 5);
            const iso = now.toISOString().slice(0, 16);
            scheduledAtInput.min = iso;
            if (!scheduledAtInput.value) {
                scheduledAtInput.value = iso;
            }
        };

        scheduleToggle.addEventListener('change', () => {
            schedulePicker.style.display = scheduleToggle.checked ? 'block' : 'none';
            if (scheduleToggle.checked) {
                setMinDatetime();
            } else {
                scheduledAtInput.value = '';
            }
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
                resetBtn(submitBtn);
                return;
            }

            if (!message) {
                showToast('Escreva sua mensagem', true);
                resetBtn(submitBtn);
                return;
            }

            // Build payload
            const payload = {
                recipient_phone: phone,
                message: message,
                sender_nickname: nickname || 'Alguem especial',
            };

            // Audio text (optional)
            if (hasAudio && audioTextInput && audioTextInput.value.trim()) {
                payload.audio_text = audioTextInput.value.trim();
            }

            // Scheduled time (optional)
            if (scheduleToggle && scheduleToggle.checked && scheduledAtInput && scheduledAtInput.value) {
                payload.scheduled_at = scheduledAtInput.value;
            }

            try {
                const resp = await fetch(`/form/${token}/submit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });

                const data = await resp.json();

                if (resp.ok) {
                    const newRemaining = data.remaining ?? 0;
                    const isScheduled = data.status === 'scheduled';

                    if (newRemaining > 0) {
                        // Partial success - more messages to send
                        showPartialSuccess(data, newRemaining, isScheduled);
                    } else {
                        // All messages sent - final success
                        showFinalSuccess(isScheduled);
                    }
                } else {
                    showToast(data.error || 'Erro ao enviar', true);
                    resetBtn(submitBtn);
                }
            } catch (err) {
                showToast('Erro de conexao', true);
                resetBtn(submitBtn);
            }
        });
    }
});

function resetBtn(btn) {
    btn.disabled = false;
    btn.textContent = '\u{1F498} Enviar Mensagem';
}

function showPartialSuccess(data, newRemaining, isScheduled) {
    const statusText = isScheduled ? 'Mensagem agendada!' : 'Mensagem enviada!';
    const statusIcon = isScheduled ? '\u{23F0}' : '\u{1F48C}';

    document.querySelector('.container').innerHTML = `
        <div class="card success-card">
            <div class="card-header">
                <div class="logo">${statusIcon}</div>
                <h1>${statusText}</h1>
                <p class="subtitle">Voce ainda tem <strong>${newRemaining}</strong> mensagem${newRemaining !== 1 ? 's' : ''} restante${newRemaining !== 1 ? 's' : ''}</p>
            </div>
            <div class="success-body">
                <p>${isScheduled ? 'Sua mensagem sera entregue no horario agendado.' : 'A pessoa especial ja recebeu no WhatsApp!'}</p>
                <button class="btn btn-primary" onclick="window.location.reload()">
                    \u{1F48C} Enviar proxima mensagem
                </button>
            </div>
        </div>
    `;
}

function showFinalSuccess(isScheduled) {
    const statusText = isScheduled ? 'Mensagem agendada!' : 'Mensagem Enviada!';
    const statusIcon = isScheduled ? '\u{23F0}' : '\u{1F48C}';
    const bodyText = isScheduled
        ? 'Sua mensagem sera entregue no horario agendado. Agora e so esperar...'
        : 'O Cupido ja entregou sua mensagem. A pessoa especial ja recebeu no WhatsApp!';

    document.querySelector('.container').innerHTML = `
        <div class="card success-card">
            <div class="card-header">
                <div class="logo">${statusIcon}</div>
                <h1>${statusText}</h1>
                <p class="subtitle">Todas as mensagens foram enviadas!</p>
            </div>
            <div class="success-body">
                <p>${bodyText}</p>
                <p class="hint">Agora e so esperar... \u{1F498}</p>
            </div>
        </div>
    `;
}

function showToast(msg, isError = false) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast ${isError ? 'error' : ''} show`;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
