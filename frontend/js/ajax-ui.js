/**
 * AJAX AI - Shared UI Components & Helpers
 * Modern Transparent Loader, Toast Notifications & Confirmation Modal
 */
(function() {
    // -------------------------------------------------------------------------
    // 1. Modern Transparent Global Loader
    // -------------------------------------------------------------------------
    let loaderEl = null;
    let loaderStatusEl = null;
    let loaderCount = 0;

    function ensureLoaderDom() {
        if (loaderEl) return;
        loaderEl = document.getElementById('globalLoader');
        if (!loaderEl) {
            loaderEl = document.createElement('div');
            loaderEl.id = 'globalLoader';
            loaderEl.className = 'ajax-global-loader';
            loaderEl.setAttribute('role', 'status');
            loaderEl.setAttribute('aria-live', 'polite');
            loaderEl.setAttribute('aria-busy', 'true');
            loaderEl.innerHTML = `
                <div class="loader-card">
                    <div class="loader-spinner-container">
                        <div class="loader-orbital-ring"></div>
                        <div class="loader-orbital-ring-inner"></div>
                        <span class="loader-icon-center">⚡</span>
                    </div>
                    <div class="loader-title">AJAX AI</div>
                    <div class="loader-status-text" id="loaderStatusText">Processing request...</div>
                </div>
            `;
            document.body.appendChild(loaderEl);
        }
        loaderStatusEl = document.getElementById('loaderStatusText');
    }

    window.showLoader = function(message = 'AJAX AI is thinking...') {
        ensureLoaderDom();
        loaderCount++;
        if (loaderStatusEl) {
            loaderStatusEl.textContent = message;
        }
        loaderEl.classList.add('visible');
    };

    window.hideLoader = function() {
        ensureLoaderDom();
        loaderCount = Math.max(0, loaderCount - 1);
        if (loaderCount === 0 && loaderEl) {
            loaderEl.classList.remove('visible');
        }
    };

    // -------------------------------------------------------------------------
    // 2. Global Toast System
    // -------------------------------------------------------------------------
    let toastContainer = null;

    function ensureToastContainer() {
        if (toastContainer) return;
        toastContainer = document.getElementById('globalToastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'globalToastContainer';
            toastContainer.className = 'ajax-toast-container';
            document.body.appendChild(toastContainer);
        }
    }

    const TOAST_ICONS = {
        info: 'ℹ️',
        success: '✅',
        warning: '⚠️',
        error: '🛑'
    };

    window.showToast = function(message, type = 'info', duration = 4000) {
        ensureToastContainer();
        const toast = document.createElement('div');
        toast.className = `ajax-toast ${type}`;
        toast.innerHTML = `
            <span class="ajax-toast-icon">${TOAST_ICONS[type] || 'ℹ️'}</span>
            <div class="ajax-toast-body">${message}</div>
            <button class="ajax-toast-close" onclick="this.parentElement.remove()">✕</button>
        `;
        toastContainer.appendChild(toast);

        // Animate in
        requestAnimationFrame(() => toast.classList.add('show'));

        // Auto dismiss
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    };

    // -------------------------------------------------------------------------
    // 3. Confirmation Modal for Dangerous Actions (CONFIRM_REQUIRED)
    // -------------------------------------------------------------------------
    let confirmModalEl = null;
    let pendingConfirmResolve = null;

    function ensureConfirmModalDom() {
        if (confirmModalEl) return;
        confirmModalEl = document.getElementById('globalConfirmModal');
        if (!confirmModalEl) {
            confirmModalEl = document.createElement('div');
            confirmModalEl.id = 'globalConfirmModal';
            confirmModalEl.className = 'ajax-modal-overlay';
            confirmModalEl.innerHTML = `
                <div class="ajax-modal-card">
                    <div class="modal-header-row">
                        <span class="modal-danger-icon">⚠️</span>
                        <h3 class="modal-title" id="confirmModalTitle">Confirm Action</h3>
                    </div>
                    <p class="modal-desc" id="confirmModalDesc">Are you sure you want to proceed?</p>
                    <div class="modal-actions-row">
                        <button class="btn-secondary" id="confirmModalCancelBtn">Cancel</button>
                        <button class="btn-danger" id="confirmModalProceedBtn">Proceed</button>
                    </div>
                </div>
            `;
            document.body.appendChild(confirmModalEl);

            document.getElementById('confirmModalCancelBtn').addEventListener('click', () => {
                closeConfirmModal(false);
            });
            document.getElementById('confirmModalProceedBtn').addEventListener('click', () => {
                closeConfirmModal(true);
            });
        }
    }

    function closeConfirmModal(result) {
        if (confirmModalEl) confirmModalEl.classList.remove('open');
        if (pendingConfirmResolve) {
            pendingConfirmResolve(result);
            pendingConfirmResolve = null;
        }
    }

    window.showConfirmModal = function({
        title = 'Confirmation Required',
        message = 'This action requires explicit authorization. Are you sure you want to continue?',
        confirmText = 'Execute',
        cancelText = 'Cancel'
    }) {
        ensureConfirmModalDom();
        document.getElementById('confirmModalTitle').textContent = title;
        document.getElementById('confirmModalDesc').textContent = message;
        document.getElementById('confirmModalProceedBtn').textContent = confirmText;
        document.getElementById('confirmModalCancelBtn').textContent = cancelText;

        confirmModalEl.classList.add('open');

        return new Promise((resolve) => {
            pendingConfirmResolve = resolve;
        });
    };

    // -------------------------------------------------------------------------
    // 4. Markdown & Chain-of-Thought (Thinking Box) Renderer
    // -------------------------------------------------------------------------
    function formatThinkingBlocks(text) {
        if (!text) return "";
        let processed = text;

        // 1. Fully closed <think>...</think> blocks
        processed = processed.replace(/<think>([\s\S]*?)<\/think>/gi, (match, thought) => {
            const thoughtClean = thought.trim();
            const thoughtHtml = window.marked ? marked.parse(thoughtClean) : thoughtClean.replace(/\n/g, '<br>');
            return `<details class="thought-accordion">
                <summary class="thought-summary">
                    <span class="thought-icon">💡</span>
                    <span class="thought-title">Reasoning Process</span>
                    <span class="thought-badge">Chain of Thought</span>
                </summary>
                <div class="thought-content">${thoughtHtml}</div>
            </details>\n\n`;
        });

        // 2. Active open <think> during live streaming
        processed = processed.replace(/<think>([\s\S]*?)$/gi, (match, thought) => {
            const thoughtClean = thought.trim();
            const thoughtHtml = window.marked ? marked.parse(thoughtClean) : thoughtClean.replace(/\n/g, '<br>');
            return `<details class="thought-accordion is-thinking" open>
                <summary class="thought-summary">
                    <span class="thought-icon thought-pulsing">⚡</span>
                    <span class="thought-title">Reasoning & Planning...</span>
                    <span class="thought-badge">Thinking</span>
                </summary>
                <div class="thought-content">${thoughtHtml}</div>
            </details>\n\n`;
        });

        return processed;
    }

    function renderMarkdown(raw) {
        if (!raw) return "";
        const withThoughts = formatThinkingBlocks(raw);
        if (window.marked) {
            try {
                marked.setOptions({
                    highlight: (code, lang) => {
                        if (window.hljs && hljs.getLanguage(lang)) {
                            return hljs.highlight(code, { language: lang }).value;
                        }
                        return code;
                    },
                    breaks: true,
                    gfm: true
                });
                return marked.parse(withThoughts);
            } catch (e) {
                return withThoughts;
    // -------------------------------------------------------------------------
    // 5. Global Speech Synthesis (Text-to-Speech Engine)
    // -------------------------------------------------------------------------
    let availableVoices = [];
    window._activeUtterance = null;
    window._ttsResumeTimer = null;

    function loadVoices() {
        if (!('speechSynthesis' in window)) return;
        try {
            const v = window.speechSynthesis.getVoices();
            if (v && v.length > 0) {
                availableVoices = v;
            }
        } catch (_) {}
    }

    if ('speechSynthesis' in window) {
        loadVoices();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = () => {
                loadVoices();
            };
        }
    }

    function cleanTextForSpeech(text) {
        if (!text) return '';
        return text
            // Strip thinking blocks <think>...</think>
            .replace(/<think>[\s\S]*?<\/think>/gi, '')
            .replace(/<think>[\s\S]*$/gi, '')
            // Strip code blocks ```...```
            .replace(/```[\s\S]*?```/gi, ' Code snippet omitted. ')
            // Strip inline code `...`
            .replace(/`([^`]+)`/g, '$1')
            // Strip HTML tags
            .replace(/<[^>]+>/g, '')
            // Strip markdown formatting symbols and URLs
            .replace(/[*#_~>]/g, '')
            .replace(/https?:\/\/\S+/gi, ' link ')
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
            // Collapse whitespaces
            .replace(/\s+/g, ' ')
            .trim();
    }

    window.speakText = function(text, lang = null) {
        if (!('speechSynthesis' in window)) {
            console.warn('[TTS] Speech synthesis not supported in this browser.');
            return;
        }

        try {
            // Cancel any pending speech safely
            window.speechSynthesis.cancel();
            if (window._ttsResumeTimer) {
                clearInterval(window._ttsResumeTimer);
                window._ttsResumeTimer = null;
            }

            const clean = cleanTextForSpeech(text);
            if (!clean) return;

            // Wait 60ms to let browser speech engine flush previous cancellations
            setTimeout(() => {
                try {
                    // Refresh voice list
                    loadVoices();
                    const voices = availableVoices.length > 0 ? availableVoices : window.speechSynthesis.getVoices();

                    // Take first 600 characters for fluid conversational speech without browser lockup
                    const speechSnippet = clean.length > 600 ? clean.substring(0, 600) + '...' : clean;

                    const utterance = new SpeechSynthesisUtterance(speechSnippet);
                    window._activeUtterance = utterance; // Prevent Chrome V8 garbage collection bug!

                    // Determine language preference
                    const currentLang = lang || (window.ajaxState ? window.ajaxState.getLanguage() : 'en');
                    
                    let chosenVoice = null;
                    if (currentLang === 'hi' && voices && voices.length > 0) {
                        // Find Hindi voice
                        chosenVoice = voices.find(v => (v.lang && v.lang.toLowerCase().startsWith('hi')) || (v.name && v.name.toLowerCase().includes('hindi')) || (v.name && (v.name.toLowerCase().includes('kalpana') || v.name.toLowerCase().includes('hemant') || v.name.toLowerCase().includes('swara') || v.name.toLowerCase().includes('madhur'))));
                    }

                    // Fallback to high-quality English / system default voice if no Hindi voice installed
                    if (!chosenVoice && voices && voices.length > 0) {
                        chosenVoice = voices.find(v => v.lang && v.lang.toLowerCase().startsWith('en') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('David') || v.name.includes('Zira') || v.name.includes('Jenny') || v.default))
                                   || voices.find(v => v.lang && v.lang.toLowerCase().startsWith('en'))
                                   || voices.find(v => v.default)
                                   || voices[0];
                    }

                    if (chosenVoice) {
                        utterance.voice = chosenVoice;
                        utterance.lang = chosenVoice.lang || (currentLang === 'hi' ? 'hi-IN' : 'en-US');
                    } else {
                        utterance.lang = currentLang === 'hi' ? 'hi-IN' : 'en-US';
                    }

                    utterance.rate = 1.0;
                    utterance.pitch = 1.0;
                    utterance.volume = 1.0;

                    utterance.onstart = () => {
                        console.log('[TTS] Speaking initiated via voice:', chosenVoice ? chosenVoice.name : 'default');
                        // Chrome 14-second cutoff keepalive
                        window._ttsResumeTimer = setInterval(() => {
                            if (window.speechSynthesis.speaking && window.speechSynthesis.paused) {
                                window.speechSynthesis.resume();
                            }
                        }, 5000);
                    };

                    utterance.onend = () => {
                        console.log('[TTS] Speech finished.');
                        if (window._ttsResumeTimer) clearInterval(window._ttsResumeTimer);
                        window._activeUtterance = null;
                    };

                    utterance.onerror = (e) => {
                        console.warn('[TTS] Speech error or interrupted:', e);
                        if (window._ttsResumeTimer) clearInterval(window._ttsResumeTimer);
                        window._activeUtterance = null;
                    };

                    // Chrome unpause fix
                    if (window.speechSynthesis.paused) {
                        window.speechSynthesis.resume();
                    }

                    window.speechSynthesis.speak(utterance);

                    // Extra fallback resume check after 100ms
                    setTimeout(() => {
                        if (window.speechSynthesis.paused) {
                            window.speechSynthesis.resume();
                        }
                    }, 100);

                } catch (innerErr) {
                    console.error('[TTS] Internal speak execution error:', innerErr);
                }
            }, 60);

        } catch (err) {
            console.error('[TTS] SpeechSynthesis error:', err);
        }
    };

    window.stopSpeech = function() {
        if ('speechSynthesis' in window) {
            try {
                if (window._ttsResumeTimer) clearInterval(window._ttsResumeTimer);
                window._activeUtterance = null;
                window.speechSynthesis.cancel();
            } catch (_) {}
        }
    };

    window.formatThinkingBlocks = formatThinkingBlocks;
    window.renderMarkdown = renderMarkdown;

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', () => {
        ensureLoaderDom();
        ensureToastContainer();
        ensureConfirmModalDom();
        loadVoices();
    });
})();
