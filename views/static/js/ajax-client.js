/**
 * AJAX AI - Unified API Client
 * Wraps backend endpoints with automatic loader, error handling & conversation syncing.
 */
(function() {
    class AjaxClient {
        constructor() {
            this.baseUrl = window.location.origin;
        }

        authHeaders(extraHeaders = {}) {
            const token = window.localStorage.getItem('ajax_session_token');
            return {
                ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
                ...extraHeaders
            };
        }

        async fetch(endpoint, options = {}) {
            const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`;
            const headers = this.authHeaders(options.headers || {});
            if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
                headers['Content-Type'] = 'application/json';
            }

            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), options.timeoutMs || 45000);
            try {
                const res = await window.fetch(url, {
                    ...options,
                    headers,
                    credentials: 'same-origin',
                    signal: options.signal || controller.signal
                });
                if (res.status === 401 && !url.includes('/api/auth/me')) {
                    window.dispatchEvent(new CustomEvent('ajax:unauthorized'));
                }
                return res;
            } finally {
                clearTimeout(timeout);
            }
        }

        async request(endpoint, options = {}, loaderMessage = null) {
            if (loaderMessage) {
                window.showLoader(loaderMessage);
            }
            try {
                const res = await this.fetch(endpoint, {
                    ...options,
                    headers: {
                        'Content-Type': 'application/json',
                        ...(options.headers || {})
                    }
                });

                if (!res.ok) {
                    let errMsg = `Request failed (HTTP ${res.status})`;
                    try {
                        const errJson = await res.json();
                        errMsg = errJson.detail || errJson.message || errMsg;
                    } catch (_) {}
                    throw new Error(errMsg);
                }

                return await res.json();
            } catch (err) {
                window.showToast(err.message || 'Network error occurred.', 'error');
                throw err;
            } finally {
                if (loaderMessage) {
                    window.hideLoader();
                }
            }
        }

        async get(endpoint, loaderMessage = null) {
            return this.request(endpoint, { method: 'GET' }, loaderMessage);
        }

        async post(endpoint, data = {}, loaderMessage = null) {
            return this.request(endpoint, {
                method: 'POST',
                body: JSON.stringify(data)
            }, loaderMessage);
        }

        /**
         * Executes an AI tool via /api/tools/execute
         */
        async executeTool(toolName, parameters = {}, confirmed = false) {
            return this.post('/api/tools/execute', {
                tool_name: toolName,
                parameters,
                confirmed
            }, `Executing tool: ${toolName}...`);
        }

        /**
         * Adds an execution result into active AI conversation and asks AI about it
         */
        askAIAboutData(contextTitle, dataPayload) {
            if (window.askAjaxAbout) {
                window.askAjaxAbout(contextTitle, dataPayload);
            } else {
                window.showToast('AI Mini-Chat is loading...', 'info');
            }
        }
    }

    window.ajaxClient = new AjaxClient();
    window.ajaxApiFetch = (endpoint, options = {}) => window.ajaxClient.fetch(endpoint, options);
})();
