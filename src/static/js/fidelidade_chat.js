/**
 * Fidelidade Chat - Polling + Send + Blur logic
 */
(function () {
    const testId = document.getElementById('test-id').value;
    const checkoutUrl = document.getElementById('checkout-url').value;
    const token = localStorage.getItem('fidelidade_token');

    if (!token) {
        window.location.href = '/fidelidade';
        return;
    }

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
    };

    const messagesEl = document.getElementById('chat-messages');
    const overlayEl = document.getElementById('blur-overlay');
    const inputAreaEl = document.getElementById('chat-input-area');
    const statusEl = document.getElementById('chat-status');
    const timerEl = document.getElementById('chat-timer');
    const unlockBtn = document.getElementById('unlock-btn');

    let lastMessageCount = 0;
    let isBlurred = true;
    let expiresAt = null;
    let timerInterval = null;

    // Set checkout URL on unlock button
    if (checkoutUrl) {
        unlockBtn.href = checkoutUrl;
    }

    // ── Fetch messages ────────────────────────────────────────

    async function fetchMessages() {
        try {
            const res = await fetch('/api/fidelidade/messages/' + testId, { headers });

            if (res.status === 401) {
                localStorage.removeItem('fidelidade_token');
                window.location.href = '/fidelidade';
                return;
            }

            const data = await res.json();
            if (!data.success) return;

            isBlurred = data.blurred;
            expiresAt = data.expires_at;

            // Update UI state
            updateUIState(data.test_status);

            // Render messages
            if (data.messages.length !== lastMessageCount) {
                renderMessages(data.messages);
                lastMessageCount = data.messages.length;
            }
        } catch (err) {
            console.error('Fetch error:', err);
        }
    }

    // ── Render messages ───────────────────────────────────────

    function renderMessages(messages) {
        if (messages.length === 0) {
            messagesEl.innerHTML = '<div class="loading-msg">Nenhuma mensagem ainda</div>';
            return;
        }

        messagesEl.innerHTML = messages.map(msg => {
            const isOut = msg.direction === 'outbound';
            const dirClass = isOut ? 'msg-outbound' : 'msg-inbound';
            const blurClass = msg.blurred ? 'msg-blurred' : '';
            const time = new Date(msg.created_at).toLocaleTimeString('pt-BR', {
                hour: '2-digit',
                minute: '2-digit'
            });

            return `
                <div class="msg-bubble ${dirClass} ${blurClass}">
                    <div class="msg-text">${escapeHtml(msg.content)}</div>
                    <div class="msg-time">${time}</div>
                </div>
            `;
        }).join('');

        // Scroll to bottom
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    // ── Update UI state ───────────────────────────────────────

    function updateUIState(testStatus) {
        if (isBlurred) {
            overlayEl.style.display = 'flex';
            inputAreaEl.style.display = 'none';

            if (testStatus === 'pending') {
                statusEl.textContent = 'Aguardando pagamento';
            } else if (testStatus === 'expired') {
                statusEl.textContent = 'Expirado';
                timerEl.style.display = 'none';
            }
        } else {
            overlayEl.style.display = 'none';
            inputAreaEl.style.display = 'block';
            statusEl.textContent = 'Ativo';

            // Start countdown timer
            if (expiresAt && !timerInterval) {
                startTimer();
            }
        }
    }

    // ── Countdown timer ───────────────────────────────────────

    function startTimer() {
        timerEl.style.display = 'block';

        function updateTimer() {
            const now = new Date();
            const exp = new Date(expiresAt);
            const diff = exp - now;

            if (diff <= 0) {
                timerEl.textContent = 'Expirado';
                timerEl.style.color = '#e63946';
                clearInterval(timerInterval);
                timerInterval = null;
                // Refresh to show locked state
                setTimeout(() => fetchMessages(), 1000);
                return;
            }

            const hours = Math.floor(diff / 3600000);
            const mins = Math.floor((diff % 3600000) / 60000);
            const secs = Math.floor((diff % 60000) / 1000);
            timerEl.textContent = `${hours}h ${String(mins).padStart(2, '0')}m ${String(secs).padStart(2, '0')}s`;
        }

        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);
    }

    // ── Send message ──────────────────────────────────────────

    document.getElementById('send-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const input = document.getElementById('message-input');
        const content = input.value.trim();
        if (!content) return;

        input.value = '';

        try {
            const res = await fetch('/api/fidelidade/messages/' + testId, {
                method: 'POST',
                headers,
                body: JSON.stringify({ content }),
            });
            const data = await res.json();
            if (data.success) {
                // Immediately refresh messages
                await fetchMessages();
            } else {
                alert(data.error || 'Erro ao enviar');
            }
        } catch (err) {
            alert('Erro de conexao');
        }
    });

    // ── Helpers ───────────────────────────────────────────────

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ── Start polling ─────────────────────────────────────────

    fetchMessages();
    setInterval(fetchMessages, 3000);
})();
