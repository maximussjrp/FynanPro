// FinanPro Advanced JavaScript

document.addEventListener('DOMContentLoaded', function() {
    initSidebar();
    initQuickTransaction();
    initAlerts();
});

// Sidebar Management
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mobileSidebarToggle = document.getElementById('mobileSidebarToggle');

    // Desktop toggle
    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('sidebar-collapsed');
            
            // Save state
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }

    // Mobile toggle
    if (mobileSidebarToggle) {
        mobileSidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
    }

    // Load saved state
    const isCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
    if (isCollapsed) {
        sidebar.classList.add('collapsed');
        mainContent.classList.add('sidebar-collapsed');
    }

    // Handle mobile view
    function handleMobileView() {
        if (window.innerWidth <= 768) {
            sidebar.classList.remove('collapsed');
            mainContent.classList.remove('sidebar-collapsed');
        } else {
            sidebar.classList.remove('open');
            if (isCollapsed) {
                sidebar.classList.add('collapsed');
                mainContent.classList.add('sidebar-collapsed');
            }
        }
    }

    window.addEventListener('resize', handleMobileView);
    handleMobileView();
}

// Quick Transaction Modal
function initQuickTransaction() {
    const quickTransactionModal = document.getElementById('quickTransactionModal');
    
    if (quickTransactionModal) {
        quickTransactionModal.addEventListener('shown.bs.modal', function() {
            // Focus on first input when modal opens
            const firstInput = quickTransactionModal.querySelector('input, select, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        });
    }
}

// Auto-dismiss alerts
function initAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert && alert.parentNode) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });
}

// Utility Functions
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

function showNotification(message, type = 'info') {
    const alertContainer = document.querySelector('.alert-container') || createAlertContainer();
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    
    const iconMap = {
        success: 'check-circle',
        danger: 'exclamation-triangle',
        warning: 'exclamation-circle',
        info: 'info-circle'
    };
    
    alertDiv.innerHTML = `
        <i class="fas fa-${iconMap[type]}"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv && alertDiv.parentNode) {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }
    }, 5000);
}

function createAlertContainer() {
    const container = document.createElement('div');
    container.className = 'alert-container';
    const pageContent = document.querySelector('.page-content');
    pageContent.insertBefore(container, pageContent.firstChild);
    return container;
}

// Form Utilities
function addFormValidation() {
    const forms = document.querySelectorAll('form[novalidate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
    });
}

// Loading States
function setLoading(element, isLoading = true) {
    if (isLoading) {
        element.classList.add('loading');
        element.disabled = true;
    } else {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

// AJAX Helper
async function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    const config = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        } else {
            return await response.text();
        }
    } catch (error) {
        console.error('Request failed:', error);
        showNotification('Erro na comunicação com o servidor', 'danger');
        throw error;
    }
}

// Search Functionality
function initSearch() {
    const searchInput = document.getElementById('globalSearch');
    
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    performSearch(query);
                }, 500);
            } else {
                clearSearchResults();
            }
        });
    }
}

function performSearch(query) {
    makeRequest(`/api/search?q=${encodeURIComponent(query)}`)
        .then(results => {
            displaySearchResults(results);
        })
        .catch(error => {
            console.error('Search failed:', error);
        });
}

function displaySearchResults(results) {
    // Implementation for displaying search results
    console.log('Search results:', results);
}

function clearSearchResults() {
    // Implementation for clearing search results
}

// Chart Utilities
function createChart(ctx, config) {
    return new Chart(ctx, {
        ...config,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            ...config.options
        }
    });
}

// Export functions for global use
window.FinanPro = {
    formatCurrency,
    formatDate,
    showNotification,
    setLoading,
    makeRequest,
    createChart
};
