/*!
* memochou - Template Initialization Module
* Handles data passed from Flask templates to JavaScript
* Copyright 2025 Tamami.K
*/

(function(window, document) {
    'use strict';

    // =============================================================================
    // TEMPLATE DATA HANDLER
    // =============================================================================

    const TemplateDataHandler = {
        // Flash messages from Flask
        initializeFlashMessages: function() {
            // This will be called from templates with actual messages
            // Messages are passed directly to the ToastManager
        },

        // Current question ID for refresh functionality
        initializeQuestionId: function(questionId) {
            window.currentQuestionId = questionId;
        },

        // Temp password warning flag
        initializeTempPasswordFlag: function(isUsing) {
            window.isUsingTempPassword = Boolean(isUsing);
        }
    };

    // =============================================================================
    // INITIALIZATION QUEUE SYSTEM
    // =============================================================================

    const InitQueue = {
        queue: [],
        isReady: false,

        add: function(fn) {
            if (this.isReady) {
                fn();
            } else {
                this.queue.push(fn);
            }
        },

        process: function() {
            this.isReady = true;
            while (this.queue.length > 0) {
                const fn = this.queue.shift();
                try {
                    fn();
                } catch (e) {
                    console.error('Error processing init queue:', e);
                }
            }
        }
    };

    // =============================================================================
    // SAFE FUNCTION CALLS
    // =============================================================================

    const SafeCall = {
        showToast: function(message, type, options) {
            InitQueue.add(function() {
                if (window.ToastManager && window.ToastManager.show) {
                    window.ToastManager.show(message, type, options);
                }
            });
        },

        showTempPasswordWarning: function() {
            InitQueue.add(function() {
                if (window.ToastManager && window.ToastManager.show) {
                    window.ToastManager.show(
                        'You are using a temporary password. Please change your password for security.',
                        'warning'
                    );
                }
            });
        }
    };

    // =============================================================================
    // PUBLIC API
    // =============================================================================

    window.memochouInit = {
        // Called when the main scripts.js is loaded
        onScriptsReady: function() {
            InitQueue.process();
        },

        // Flash messages handler
        showFlashMessages: function(messages) {
            if (messages && messages.length > 0) {
                messages.forEach(function(message) {
                    let type = 'info';
                    const lowerMessage = message.toLowerCase();
                    
                    if (lowerMessage.includes('error') || lowerMessage.includes('failed')) {
                        type = 'error';
                    } else if (lowerMessage.includes('warning')) {
                        type = 'warning';
                    } else if (lowerMessage.includes('success') || lowerMessage.includes('successfully')) {
                        type = 'success';
                    }
                    
                    SafeCall.showToast(message, type);
                });
            }
        },

        // Temp password warning
        showTempPasswordWarning: function() {
            SafeCall.showTempPasswordWarning();
        },

        // Set question ID
        setQuestionId: function(questionId) {
            TemplateDataHandler.initializeQuestionId(questionId);
        },

        // Set temp password flag
        setTempPasswordFlag: function(flag) {
            TemplateDataHandler.initializeTempPasswordFlag(flag);
        }
    };

    // =============================================================================
    // AUTO-INITIALIZATION
    // =============================================================================

    // Mark as ready when scripts.js loads (if it hasn't already)
    document.addEventListener('DOMContentLoaded', function() {
        // Give scripts.js time to load
        setTimeout(function() {
            if (!InitQueue.isReady && window.App) {
                InitQueue.process();
            }
        }, 100);
    });

    // Also check if scripts.js is already loaded
    if (window.App) {
        InitQueue.process();
    }

})(window, document);
