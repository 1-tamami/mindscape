/*!
* memochou - Self-reflection Blog Service
* Enhanced JavaScript functionality
* Copyright 2025 Tamami.K
*/

// =============================================================================
// CONFIGURATION AND CONSTANTS
// =============================================================================

const CONFIG = {
    CHAR_LIMIT: 2000,
    TOAST_DURATION: 5000,
    TOOLTIP_OFFSET: 8,
    SCROLL_BEHAVIOR: 'smooth'
};

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

const Utils = {
    saveScrollPosition() {
        sessionStorage.setItem('scrollPosition', window.pageYOffset);
    },

    restoreScrollPosition() {
        const scrollPosition = sessionStorage.getItem('scrollPosition');
        if (scrollPosition) {
            window.scrollTo(0, parseInt(scrollPosition));
            sessionStorage.removeItem('scrollPosition');
        }
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// =============================================================================
// TOAST NOTIFICATION SYSTEM
// =============================================================================

const ToastManager = {
    show(message, type = 'info', options = {}) {
        const toastElement = document.getElementById('toastMessage');
        const toastBody = document.getElementById('toastBodyContent');
        
        if (!toastElement || !toastBody) return;

        // Support HTML content for links
        if (options.html) {
            toastBody.innerHTML = message;
        } else {
            toastBody.textContent = message;
        }
        
        const typeClasses = {
            success: 'text-bg-success',
            error: 'text-bg-danger',
            warning: 'text-bg-warning',
            info: 'text-bg-info'
        };
        
        toastElement.className = `toast align-items-center border-0 ${typeClasses[type] || typeClasses.info}`;
        
        // Determine autohide based on options
        const autohide = options.autohide !== undefined ? options.autohide : true;
        
        const toast = bootstrap.Toast.getOrCreateInstance(toastElement, {
            autohide: autohide,
            delay: CONFIG.TOAST_DURATION
        });
        toast.show();
    }
};

// =============================================================================
// TOOLTIP SYSTEM
// =============================================================================

const TooltipManager = {
    tooltips: new Map(),

    initialize() {
        const tooltipTriggers = document.querySelectorAll('.tooltip-trigger');
        
        tooltipTriggers.forEach(trigger => {
            const tooltip = this.createTooltip();
            this.tooltips.set(trigger, tooltip);
            
            trigger.addEventListener('mouseenter', (e) => {
                const text = trigger.getAttribute('data-tooltip') || trigger.getAttribute('title');
                if (text) {
                    this.show(tooltip, text, e.target);
                }
            });
            
            trigger.addEventListener('mouseleave', () => {
                this.hide(tooltip);
            });
            
            trigger.addEventListener('click', () => {
                this.hide(tooltip);
            });
        });
    },

    createTooltip() {
        const tooltip = document.createElement('div');
        tooltip.className = 'custom-tooltip';
        document.body.appendChild(tooltip);
        return tooltip;
    },

    show(tooltip, text, targetElement) {
        tooltip.textContent = text;
        tooltip.style.opacity = '0';
        tooltip.style.display = 'block';
        
        const rect = targetElement.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();
        
        let top = rect.top - tooltipRect.height - CONFIG.TOOLTIP_OFFSET;
        let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
        
        if (top < 0) {
            top = rect.bottom + CONFIG.TOOLTIP_OFFSET;
        }
        if (left < 0) {
            left = CONFIG.TOOLTIP_OFFSET;
        }
        if (left + tooltipRect.width > window.innerWidth) {
            left = window.innerWidth - tooltipRect.width - CONFIG.TOOLTIP_OFFSET;
        }
        
        tooltip.style.top = top + window.scrollY + 'px';
        tooltip.style.left = left + 'px';
        tooltip.style.opacity = '1';
    },

    hide(tooltip) {
        tooltip.style.opacity = '0';
        setTimeout(() => {
            tooltip.style.display = 'none';
        }, 200);
    },

    cleanup() {
        this.tooltips.forEach(tooltip => {
            tooltip.remove();
        });
        this.tooltips.clear();
    }
};

// =============================================================================
// PUBLIC/PRIVATE TOGGLE FUNCTIONALITY
// =============================================================================

const PublicToggle = {
    isPublic: true,

    initialize(initialState = true) {
        this.isPublic = initialState;
        this.updateUI();
    },

    toggle() {
        this.isPublic = !this.isPublic;
        this.updateUI();
    },

    updateUI() {
        const button = document.getElementById('publicToggle');
        const input = document.getElementById('isPublicInput');
        
        if (!button || !input) return;

        const tooltip = button.querySelector('[data-tooltip]') || button;
        
        if (this.isPublic) {
            button.style.opacity = '1';
            button.style.backgroundColor = '#000';
            input.value = '1';
            tooltip.setAttribute('data-tooltip', 'Public');
            tooltip.setAttribute('title', 'Public');
        } else {
            button.style.opacity = '0.6';
            button.style.backgroundColor = '#6c757d';
            input.value = '0';
            tooltip.setAttribute('data-tooltip', 'Private');
            tooltip.setAttribute('title', 'Private');
        }
    }
};

// =============================================================================
// QUESTION REFRESH FUNCTIONALITY
// =============================================================================

const QuestionManager = {
    async refresh() {
        try {
            const currentQuestionId = window.currentQuestionId;
            if (!currentQuestionId) {
                throw new Error('No current question ID found');
            }

            const response = await fetch(`/refresh_question?exclude=${currentQuestionId}`);
            const data = await response.json();
            
            if (data.success) {
                location.reload();
            } else {
                ToastManager.show('Failed to get a new question. Please try again.', 'error');
            }
        } catch (error) {
            console.error('Error refreshing question:', error);
            ToastManager.show('Failed to get a new question. Please try again.', 'error');
        }
    }
};

// =============================================================================
// PROFILE DROPDOWN FUNCTIONALITY
// =============================================================================

const ProfileDropdown = {
    toggle() {
        const dropdown = document.getElementById('profileDropdown');
        if (dropdown) {
            dropdown.classList.toggle('show');
        }
    },

    initialize() {
        document.addEventListener('click', (event) => {
            const dropdown = document.getElementById('profileDropdown');
            const profileImage = document.querySelector('.profile-image');
            
            if (dropdown && !dropdown.contains(event.target) && event.target !== profileImage) {
                dropdown.classList.remove('show');
            }
        });
    }
};

// =============================================================================
// FORM ENHANCEMENTS
// =============================================================================

const FormManager = {
    initialize() {
        this.setupTextareaAutoResize();
        this.setupFormSubmissionLoading();
        this.setupDeleteConfirmation();
        this.setupCharacterLimits();
    },

    setupTextareaAutoResize() {
        const textareas = document.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = (this.scrollHeight) + 'px';
            });
        });
    },

    setupFormSubmissionLoading() {
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', function() {
                const submitButton = this.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = true;
                    const originalText = submitButton.innerHTML;
                    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Submitting...';
                    
                    setTimeout(() => {
                        submitButton.disabled = false;
                        submitButton.innerHTML = originalText;
                    }, 5000);
                }
            });
        });
    },

    setupDeleteConfirmation() {
        const deleteLinks = document.querySelectorAll('a[href*="delete="], button[onclick*="delete"]');
        deleteLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
                    e.preventDefault();
                }
            });
        });
    },

    setupCharacterLimits() {
        const textareas = document.querySelectorAll('textarea[data-char-limit]');
        textareas.forEach(textarea => {
            const limit = parseInt(textarea.getAttribute('data-char-limit')) || CONFIG.CHAR_LIMIT;
            this.addCharacterCounter(textarea, limit);
        });
    },

    addCharacterCounter(textarea, limit) {
        const counter = document.createElement('div');
        counter.className = 'character-counter text-muted small text-end mt-1';
        counter.style.fontSize = '0.8rem';
        
        const updateCounter = () => {
            const remaining = limit - textarea.value.length;
            counter.textContent = `${textarea.value.length}/${limit}`;
            
            if (remaining < 50) {
                counter.style.color = '#dc3545';
            } else if (remaining < 100) {
                counter.style.color = '#ffc107';
            } else {
                counter.style.color = '#6c757d';
            }
        };
        
        textarea.addEventListener('input', updateCounter);
        textarea.parentNode.appendChild(counter);
        updateCounter();
    }
};

// =============================================================================
// PROFILE IMAGE MANAGEMENT
// =============================================================================

const ProfileImageManager = {
    remove() {
        if (!confirm('Are you sure you want to remove your profile image?')) {
            return;
        }

        const removeField = document.getElementById('removeProfileImageField');
        if (removeField) {
            removeField.checked = true;
        }
        
        const img = document.querySelector('.rounded-circle');
        if (img) {
            img.src = "/static/assets/img/default_user.svg";
        }
        
        const removeBtn = document.querySelector('.profile-remove-btn, .profile-remove-btn-black');
        if (removeBtn) {
            removeBtn.style.display = 'none';
        }
        
        this.showFeedback('Profile image will be removed when you save.');
        
        const form = document.querySelector('form');
        if (form) {
            form.submit();
        }
    },

    showFeedback(message) {
        const feedback = document.createElement('div');
        feedback.className = 'alert alert-info mt-2';
        feedback.innerHTML = `<i class="bi bi-info-circle me-2"></i>${message}`;
        
        const container = document.querySelector('.col-md-3') || document.querySelector('.profile-image-container');
        if (container) {
            container.appendChild(feedback);
        }
    }
};

// =============================================================================
// FLASK INTEGRATION AND DATA HANDLING
// =============================================================================

const FlaskDataHandler = {
    initializeFromTemplate() {
        // This function should be called from inline scripts in templates
        // to pass server-side data to JavaScript
        
        // Flash messages handling
        if (typeof window.flashMessages !== 'undefined' && window.flashMessages.length > 0) {
            App.handleFlashMessages();
        }
        
        // Temp password warning
        if (typeof window.isUsingTempPassword !== 'undefined' && window.isUsingTempPassword) {
            App.handleTempPasswordWarning();
        }
        
        // Current question ID from template
        if (typeof window.currentQuestionId !== 'undefined') {
            // Already handled in App.initializePageSpecific()
        }
    },

    setFlashMessages(messages) {
        window.flashMessages = messages || [];
        
        // Process messages immediately if App is ready
        if (typeof App !== 'undefined' && App.handleFlashMessages) {
            App.handleFlashMessages();
        }
    },

    setTempPasswordFlag(flag) {
        window.isUsingTempPassword = Boolean(flag);
        
        // Show warning immediately if App is ready
        if (flag && typeof App !== 'undefined' && App.handleTempPasswordWarning) {
            App.handleTempPasswordWarning();
        }
    },

    setCurrentQuestionId(questionId) {
        window.currentQuestionId = questionId;
    }
};

// =============================================================================
// MAIN APPLICATION INITIALIZATION
// =============================================================================

const App = {
    init() {
        console.log('memochou App initializing...');
        
        TooltipManager.initialize();
        ProfileDropdown.initialize();
        FormManager.initialize();
        
        this.initializePageSpecific();
        this.initializeGlobalVariables();
        this.handleFlashMessages();
        this.handleTempPasswordWarning();
        Utils.restoreScrollPosition();
        
        console.log('memochou App initialized successfully');
    },

    initializePageSpecific() {
        // Question page with public toggle
        if (document.getElementById('publicToggle')) {
            const initialState = document.getElementById('isPublicInput')?.value === '1';
            PublicToggle.initialize(initialState);
        }

        // Edit page with existing answer
        if (window.location.pathname.includes('/edit=')) {
            const isPublicValue = document.getElementById('isPublicInput')?.value;
            PublicToggle.initialize(isPublicValue === '1');
        }

        // Set current question ID for refresh functionality
        const questionIdElement = document.querySelector('[data-question-id]');
        if (questionIdElement) {
            window.currentQuestionId = questionIdElement.getAttribute('data-question-id');
        }
    },

    initializeGlobalVariables() {
        // Initialize flash messages from inline scripts
        if (typeof window.flashMessages === 'undefined') {
            window.flashMessages = [];
        }
        
        // Initialize temp password flag
        if (typeof window.isUsingTempPassword === 'undefined') {
            window.isUsingTempPassword = false;
        }
        
        // Initialize current question ID if present in URL
        if (!window.currentQuestionId) {
            const pathMatch = window.location.pathname.match(/post=(\d+)/);
            if (pathMatch) {
                window.currentQuestionId = parseInt(pathMatch[1]);
            }
        }
    },

    handleFlashMessages() {
        if (window.flashMessages && window.flashMessages.length > 0) {
            window.flashMessages.forEach(message => {
                let type = 'info';
                const lowerMessage = message.toLowerCase();
                
                if (lowerMessage.includes('error') || lowerMessage.includes('failed')) {
                    type = 'error';
                } else if (lowerMessage.includes('warning')) {
                    type = 'warning';
                } else if (lowerMessage.includes('success') || lowerMessage.includes('successfully')) {
                    type = 'success';
                }
                
                ToastManager.show(message, type);
            });
        }
    },

    handleTempPasswordWarning() {
        if (window.isUsingTempPassword) {
            ToastManager.show('You are using a temporary password. Please change your password for security.', 'warning');
        }
    }
};

// =============================================================================
// GLOBAL FUNCTIONS (for backwards compatibility)
// =============================================================================

window.togglePublic = () => PublicToggle.toggle();
window.refreshQuestion = () => QuestionManager.refresh();
window.toggleProfileDropdown = () => ProfileDropdown.toggle();
window.removeProfileImage = () => ProfileImageManager.remove();
window.saveScrollPosition = () => Utils.saveScrollPosition();

// =============================================================================
// APPLICATION STARTUP
// =============================================================================

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        App.init();
        // Notify init.js that scripts are ready
        if (window.memochouInit && window.memochouInit.onScriptsReady) {
            window.memochouInit.onScriptsReady();
        }
    });
} else {
    App.init();
    // Notify init.js that scripts are ready
    if (window.memochouInit && window.memochouInit.onScriptsReady) {
        window.memochouInit.onScriptsReady();
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    TooltipManager.cleanup();
});

// Expose Flask data handler globally
window.FlaskDataHandler = FlaskDataHandler;

// Export for potential module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        App,
        ToastManager,
        TooltipManager,
        PublicToggle,
        QuestionManager,
        ProfileDropdown,
        FormManager,
        ProfileImageManager,
        Utils,
        CONFIG,
        FlaskDataHandler
    };
}
