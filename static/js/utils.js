/**
 * Utility functions for Chat Application
 */

/**
 * Safe array access - handles multiple response formats
 */
function safeArray(data) {
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.results)) return data.results;
    if (data && Array.isArray(data.data)) return data.data;
    if (data && data.data && Array.isArray(data.data.items)) return data.data.items;
    return [];
}

/**
 * Safe object access with dot notation
 */
function safeGet(obj, path, defaultValue = null) {
    try {
        return path.split('.').reduce((o, p) => o?.[p], obj) ?? defaultValue;
    } catch (e) {
        return defaultValue;
    }
}

/**
 * Format date to readable string
 */
function formatDate(dateString) {
    try {
        return new Date(dateString).toLocaleDateString();
    } catch (e) {
        return 'Unknown date';
    }
}

/**
 * Format time to readable string
 */
function formatTime(dateString) {
    try {
        return new Date(dateString).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (e) {
        return 'Unknown time';
    }
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHTML(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

/**
 * Truncate text with ellipsis
 */
function truncate(text, length = 30) {
    if (!text) return '';
    const str = String(text);
    return str.length > length ? str.substring(0, length) + '...' : str;
}

/**
 * Group array by key function
 */
function groupBy(array, keyFn) {
    return array.reduce((groups, item) => {
        try {
            const key = keyFn(item);
            if (!groups[key]) groups[key] = [];
            groups[key].push(item);
        } catch (e) {
            console.error('Error grouping item:', item, e);
        }
        return groups;
    }, {});
}

/**
 * Show notification to user
 */
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'error' ? '#f8d7da' : type === 'success' ? '#d4edda' : '#d1ecf1'};
        color: ${type === 'error' ? '#721c24' : type === 'success' ? '#155724' : '#0c5460'};
        border: 1px solid ${type === 'error' ? '#f5c6cb' : type === 'success' ? '#c3e6cb' : '#bee5eb'};
        border-radius: 6px;
        z-index: 9999;
        max-width: 400px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

/**
 * Show error notification
 */
function showError(message) {
    showNotification(message, 'error');
}

/**
 * Show success notification
 */
function showSuccess(message) {
    showNotification(message, 'success');
}

/**
 * Show info notification
 */
function showInfo(message) {
    showNotification(message, 'info');
}

/**
 * Debounce function
 */
function debounce(func, wait) {
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

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!localStorage.getItem('accessToken');
}

/**
 * Get current user info
 */
function getCurrentUser() {
    return {
        id: parseInt(localStorage.getItem('userId')),
        username: localStorage.getItem('username'),
        token: localStorage.getItem('accessToken')
    };
}

/**
 * Logout user
 */
function logout() {
    localStorage.clear();
    window.location.href = '/';
}

/**
 * Redirect to login if not authenticated
 */
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login/';
    }
}

/**
 * Create element with attributes
 */
function createElement(tag, attributes = {}, content = '') {
    const element = document.createElement(tag);
    Object.entries(attributes).forEach(([key, value]) => {
        if (key === 'class') {
            element.className = value;
        } else if (key === 'style') {
            Object.assign(element.style, value);
        } else {
            element.setAttribute(key, value);
        }
    });
    if (content) {
        element.innerHTML = content;
    }
    return element;
}

/**
 * Clear element children
 */
function clearElement(element) {
    while (element.firstChild) {
        element.removeChild(element.firstChild);
    }
}

/**
 * Add loading spinner to element
 */
function showLoading(element) {
    clearElement(element);
    const spinner = createElement('div', { class: 'loading' });
    spinner.innerHTML = '<span class="spinner"></span> Loading...';
    element.appendChild(spinner);
}

/**
 * Show empty state message
 */
function showEmpty(element, message = 'No items found') {
    clearElement(element);
    const empty = createElement('div', {
        style: {
            padding: '20px',
            textAlign: 'center',
            color: '#999'
        }
    }, message);
    element.appendChild(empty);
}

/**
 * Show error message in element
 */
function showErrorInElement(element, message = 'An error occurred') {
    clearElement(element);
    const error = createElement('div', {
        style: {
            padding: '20px',
            textAlign: 'center',
            color: '#721c24',
            background: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '6px'
        }
    }, message);
    element.appendChild(error);
}
