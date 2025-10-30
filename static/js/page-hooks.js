(function () {
    /**
     * Safely parse a JSON string into an object/array.
     * Returns an empty array when parsing fails.
     */
    function parseMessages(raw) {
        if (!raw || raw === 'null' || raw === 'undefined') {
            return [];
        }

        try {
            var parsed = JSON.parse(raw);
            return Array.isArray(parsed) ? parsed : [];
        } catch (error) {
            console.warn('Unable to parse flash messages payload.', error);
            return [];
        }
    }

    /**
     * Invoke a memochouInit function only when it exists.
     */
    function callInitMethod(methodName, args) {
        if (window.memochouInit && typeof window.memochouInit[methodName] === 'function') {
            window.memochouInit[methodName].apply(window.memochouInit, args || []);
        }
    }

    function handleFlashMessages(body) {
        var messages = parseMessages(body.dataset.flashMessages);
        if (messages.length > 0) {
            callInitMethod('showFlashMessages', [messages]);
        }
    }

    function handleTempPasswordAlert(body) {
        var isUsingTempPassword = body.dataset.usingTempPassword === 'true';
        if (isUsingTempPassword) {
            callInitMethod('setTempPasswordFlag', [true]);
            callInitMethod('showTempPasswordWarning');
        }
    }

    function initialize() {
        var body = document.body;
        if (!body) {
            return;
        }

        handleFlashMessages(body);
        handleTempPasswordAlert(body);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
})();
