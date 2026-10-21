/**
 * AJAX AI - Shared Application State Manager
 * Persists and syncs active conversation, language, voice, and web-search preferences.
 */
(function() {
    const STORAGE_KEY_CONV = 'ajax_active_conversation_id';
    const STORAGE_KEY_LANG = 'ajax_language_pref';
    const STORAGE_KEY_VOICE = 'ajax_voice_speech_enabled';
    const STORAGE_KEY_WEB = 'ajax_web_search_enabled';

    class AjaxStateManager {
        constructor() {
            this.conversationId = localStorage.getItem(STORAGE_KEY_CONV) || '';
            this.language = localStorage.getItem(STORAGE_KEY_LANG) || 'en';
            this.voiceEnabled = localStorage.getItem(STORAGE_KEY_VOICE) === 'true';
            this.webSearchEnabled = localStorage.getItem(STORAGE_KEY_WEB) === 'true';

            // Ensure a valid conversation session exists or generate one
            if (!this.conversationId) {
                this.conversationId = 'conv_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now();
                localStorage.setItem(STORAGE_KEY_CONV, this.conversationId);
            }
        }

        getConversationId() {
            return this.conversationId;
        }

        setConversationId(id) {
            if (!id) return;
            this.conversationId = id;
            localStorage.setItem(STORAGE_KEY_CONV, id);
            this._notify('conversation_change', { conversationId: id });
        }

        getLanguage() {
            return this.language;
        }

        setLanguage(lang) {
            this.language = lang === 'hi' ? 'hi' : 'en';
            localStorage.setItem(STORAGE_KEY_LANG, this.language);
            this._notify('language_change', { language: this.language });
        }

        toggleLanguage() {
            const nextLang = this.language === 'en' ? 'hi' : 'en';
            this.setLanguage(nextLang);
            return nextLang;
        }

        isVoiceEnabled() {
            return this.voiceEnabled;
        }

        setVoiceEnabled(enabled) {
            this.voiceEnabled = !!enabled;
            localStorage.setItem(STORAGE_KEY_VOICE, String(this.voiceEnabled));
            this._notify('voice_change', { voiceEnabled: this.voiceEnabled });
        }

        toggleVoice() {
            this.setVoiceEnabled(!this.voiceEnabled);
            return this.voiceEnabled;
        }

        isWebSearchEnabled() {
            return this.webSearchEnabled;
        }

        setWebSearchEnabled(enabled) {
            this.webSearchEnabled = !!enabled;
            localStorage.setItem(STORAGE_KEY_WEB, String(this.webSearchEnabled));
            this._notify('web_search_change', { webSearchEnabled: this.webSearchEnabled });
        }

        _notify(type, detail) {
            window.dispatchEvent(new CustomEvent('ajax:state-change', { detail: { type, ...detail } }));
        }
    }

    window.ajaxState = new AjaxStateManager();
})();
