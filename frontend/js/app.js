/**
 * Global App utilities
 */

const App = {
    // Utility to show toasts
    showToast: function(title, message, type = 'success') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(container);
        }

        const bgClass = type === 'success' ? 'bg-success text-white' : (type === 'danger' ? 'bg-danger text-white' : 'bg-primary text-white');
        
        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center border-0 ${bgClass}`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        
        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <strong>${title}</strong><br>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        document.getElementById('toast-container').appendChild(toastEl);
        
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    },

    // Format currency
    formatCurrency: function(amount) {
        return '₹' + parseFloat(amount).toFixed(2);
    },

    // Populate user profile dropdown in navbar
    initNavbar: function() {
        const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
        const loginLinks = document.getElementById('nav-login-links');
        const userLinks = document.getElementById('nav-user-links');
        
        if (isLoggedIn) {
            if(loginLinks) loginLinks.classList.add('d-none');
            if(userLinks) userLinks.classList.remove('d-none');
        } else {
            if(loginLinks) loginLinks.classList.remove('d-none');
            if(userLinks) userLinks.classList.add('d-none');
        }
    },

    logout: function() {
        localStorage.removeItem('isLoggedIn');
        window.location.href = '/frontend/index.html';
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.initNavbar();
});
