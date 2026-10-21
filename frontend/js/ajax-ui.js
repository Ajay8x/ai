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

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', () => {
        ensureLoaderDom();
        ensureToastContainer();
        ensureConfirmModalDom();
    });
})();
