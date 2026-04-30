const pingForm = document.getElementById('pingForm');
const hostnameInput = document.getElementById('hostname');
const apiModal = document.getElementById('apiModal');


document.addEventListener('DOMContentLoaded', () => {
    
    hostnameInput?.focus();

    pingForm?.addEventListener('submit', handleFormSubmit);
    apiModal?.addEventListener('click', (e) => {
        if (e.target === apiModal) {
            closeApiDocs();
        }
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeApiDocs();
        }
    });
});
e
function handleFormSubmit(e) {
    const btn = pingForm.querySelector('.btn-primary');
    const originalText = btn.innerHTML;

    pingForm.classList.add('loading');
    btn.disabled = true;
    btn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 2a10 10 0 0 1 10 10"/>
            <path d="M12 12l4-4"/>
            <path d="M12 12v6"/>
        </svg>
        <span>جاري الاختبار...</span>
    `;

   setTimeout(() => {
        btn.disabled = false;
        pingForm.classList.remove('loading');
        btn.innerHTML = originalText;
    }, 500);
}

async function copyOutput() {
    const output = document.getElementById('output');
    if (!output) return;

    try {
        await navigator.clipboard.writeText(output.textContent);
        showToast('copied to clipboard!');
    } catch (err) {
        const range = document.createRange();
        range.selectNode(output);
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
        document.execCommand('copy');
        window.getSelection().removeAllRanges();
        showToast('copied to clipboard!');
    }
}

function showToast(message) {
    // Remove existing toast
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 24px;
        left: 50%;
        transform: translateX(-50%);
        background: #10b981;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        z-index: 10000;
        animation: slideUp 0.3s ease;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideDown 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

function showApiDocs() {
    apiModal?.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeApiDocs() {
    apiModal?.classList.remove('active');
    document.body.style.overflow = '';
}

const style = document.createElement('style');
style.textContent = `
    @keyframes slideUp {
        from { opacity: 0; transform: translateX(-50%) translateY(20px); }
        to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
    @keyframes slideDown {
        from { opacity: 1; transform: translateX(-50%) translateY(0); }
        to { opacity: 0; transform: translateX(-50%) translateY(20px); }
    }
`;
document.head.appendChild(style);
