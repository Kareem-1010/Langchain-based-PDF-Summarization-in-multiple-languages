// Main JavaScript file for common functionality

// Notification System
function showNotification(message, type = 'info') {
    const toast = document.getElementById('notificationToast');
    const toastBody = toast.querySelector('.toast-body');
    const toastHeader = toast.querySelector('.toast-header');
    
    // Remove previous type classes
    toast.classList.remove('bg-success', 'bg-danger', 'bg-warning', 'bg-info');
    
    // Set message
    toastBody.textContent = message;
    
    // Set type-specific styling
    let icon = 'bi-info-circle';
    let headerClass = 'text-primary';
    
    switch(type) {
        case 'success':
            icon = 'bi-check-circle';
            headerClass = 'text-success';
            break;
        case 'error':
            icon = 'bi-exclamation-triangle';
            headerClass = 'text-danger';
            break;
        case 'warning':
            icon = 'bi-exclamation-circle';
            headerClass = 'text-warning';
            break;
    }
    
    // Update icon
    const iconElement = toastHeader.querySelector('i');
    iconElement.className = `bi ${icon} me-2 ${headerClass}`;
    
    // Show toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 3000
    });
    bsToast.show();
}

// Sidebar Toggle for Mobile
document.addEventListener('DOMContentLoaded', function() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', function(event) {
            const isClickInside = sidebar.contains(event.target) || sidebarToggle.contains(event.target);
            
            if (!isClickInside && window.innerWidth <= 992) {
                sidebar.classList.remove('show');
            }
        });
    }
});

// Form validation helper
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Loading state helper
function setLoadingState(button, isLoading, loadingText = 'Loading...') {
    if (isLoading) {
        button.disabled = true;
        button.dataset.originalText = button.textContent;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            ${loadingText}
        `;
    } else {
        button.disabled = false;
        button.textContent = button.dataset.originalText || 'Submit';
    }
}

// Debounce helper for search inputs
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

// Format date helper
function formatDate(dateString) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

// Copy to clipboard helper
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copied to clipboard!', 'success');
        }).catch(() => {
            showNotification('Failed to copy', 'error');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showNotification('Copied to clipboard!', 'success');
        } catch (err) {
            showNotification('Failed to copy', 'error');
        }
        document.body.removeChild(textArea);
    }
}

// Error handler for fetch requests
async function handleFetchError(response) {
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.message || 'An error occurred');
    }
    return response.json();
}

// Make functions available globally
window.showNotification = showNotification;
window.validateEmail = validateEmail;
window.setLoadingState = setLoadingState;
window.debounce = debounce;
window.formatDate = formatDate;
window.copyToClipboard = copyToClipboard;
window.handleFetchError = handleFetchError;
