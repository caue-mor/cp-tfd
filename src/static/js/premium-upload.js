// Cupido - Premium upload (drag-drop images + captions)

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('premium-form');
    if (!form) return;

    const token = document.getElementById('form-token').value;
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('preview-container');
    let selectedFiles = [];

    // Click to select
    dropZone.addEventListener('click', () => fileInput.click());

    // Drag events
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        addFiles(Array.from(e.dataTransfer.files));
    });

    fileInput.addEventListener('change', () => {
        addFiles(Array.from(fileInput.files));
        fileInput.value = '';
    });

    function addFiles(files) {
        const imageFiles = files.filter(f => f.type.startsWith('image/'));
        if (selectedFiles.length + imageFiles.length > 10) {
            showToast('Maximo 10 imagens', true);
            return;
        }
        selectedFiles.push(...imageFiles);
        renderPreviews();
    }

    function renderPreviews() {
        previewContainer.innerHTML = '';
        selectedFiles.forEach((file, i) => {
            const div = document.createElement('div');
            div.className = 'preview-item';

            const img = document.createElement('img');
            img.src = URL.createObjectURL(file);

            const removeBtn = document.createElement('button');
            removeBtn.className = 'remove-btn';
            removeBtn.textContent = 'X';
            removeBtn.onclick = () => {
                selectedFiles.splice(i, 1);
                renderPreviews();
            };

            const captionInput = document.createElement('input');
            captionInput.type = 'text';
            captionInput.placeholder = 'Legenda...';
            captionInput.dataset.index = i;
            captionInput.className = 'caption-input';

            div.appendChild(img);
            div.appendChild(removeBtn);
            div.appendChild(captionInput);
            previewContainer.appendChild(div);
        });
    }

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

    // Audio char counter for premium
    const premiumAudioInput = document.getElementById('premium_audio_text');
    const premiumAudioCount = document.getElementById('premium-audio-char-count');
    if (premiumAudioInput && premiumAudioCount) {
        premiumAudioInput.addEventListener('input', () => {
            premiumAudioCount.textContent = premiumAudioInput.value.length;
        });
    }

    // Submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = document.getElementById('submit-btn');

        if (selectedFiles.length === 0) {
            showToast('Selecione pelo menos uma imagem', true);
            return;
        }

        const phone = phoneInput.value.replace(/\D/g, '');
        if (phone.length < 10) {
            showToast('Telefone invalido', true);
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Enviando...';

        // Collect captions
        const captions = [];
        document.querySelectorAll('.caption-input').forEach(input => {
            captions.push(input.value || '');
        });

        const formData = new FormData();
        formData.append('recipient_phone', phone);
        formData.append('title', document.getElementById('title').value);
        formData.append('sender_nickname', document.getElementById('sender_nickname').value);
        formData.append('slides_data', JSON.stringify(captions));

        // Audio text (optional)
        if (premiumAudioInput && premiumAudioInput.value.trim()) {
            formData.append('audio_text', premiumAudioInput.value.trim());
        }

        selectedFiles.forEach(file => {
            formData.append('files', file);
        });

        try {
            const resp = await fetch(`/form/${token}/upload`, {
                method: 'POST',
                body: formData,
            });

            const data = await resp.json();

            if (resp.ok) {
                document.querySelector('.container').innerHTML = `
                    <div class="card success-card">
                        <div class="card-header">
                            <div class="logo">💌</div>
                            <h1>Apresentacao Enviada!</h1>
                            <p class="subtitle">O Cupido ja entregou o link especial</p>
                        </div>
                        <div class="success-body">
                            <p>A pessoa especial recebeu um link com sua apresentacao!</p>
                            <p class="hint">Agora e so esperar... 💘</p>
                        </div>
                    </div>
                `;
            } else {
                showToast(data.error || 'Erro ao enviar', true);
                submitBtn.disabled = false;
                submitBtn.textContent = '💘 Enviar Apresentacao';
            }
        } catch (err) {
            showToast('Erro de conexao', true);
            submitBtn.disabled = false;
            submitBtn.textContent = '💘 Enviar Apresentacao';
        }
    });
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
