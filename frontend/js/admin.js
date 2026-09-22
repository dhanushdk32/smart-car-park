/**
 * Admin logic and interactions
 */

const AppAdmin = {
    handleLogin: async function() {
        const emailInput = document.getElementById('adminEmail');
        const passwordInput = document.getElementById('adminPassword');
        const errorAlert = document.getElementById('loginErrorAlert');

        const identifier = emailInput ? emailInput.value.trim() : '';
        const password = passwordInput ? passwordInput.value : '';

        if (!identifier || !password) {
            this.showError("Please enter both username/email and password");
            return;
        }

        const submitBtn = document.querySelector('#adminLoginForm button[type="submit"]');
        const originalText = submitBtn ? submitBtn.innerHTML : 'Login';
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Authenticating...';
        }

        try {
            const data = await window.Api.login(identifier, password);
            if (!data.user || data.user.role !== 'admin') {
                window.Api.removeToken();
                throw new Error("Access denied: You do not have Administrator permissions.");
            }

            localStorage.setItem('adminLoggedIn', 'true');
            window.location.href = 'dashboard.html';
        } catch (err) {
            console.error("Admin Login Error:", err);
            this.showError(err.message || "Invalid credentials or unauthorized.");
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }
        }
    },

    showError: function(msg) {
        let alert = document.getElementById('loginErrorAlert');
        if (!alert) {
            alert = document.createElement('div');
            alert.id = 'loginErrorAlert';
            alert.className = 'alert alert-danger py-2 px-3 small mt-3 mb-0 rounded-3';
            const form = document.getElementById('adminLoginForm');
            if (form) form.appendChild(alert);
        }
        alert.textContent = msg;
        alert.classList.remove('d-none');
    },

    logout: function() {
        window.Api.removeToken();
        localStorage.removeItem('adminLoggedIn');
        window.location.href = 'login.html';
    },

    toggleSidebar: function() {
        const sidebar = document.getElementById('adminSidebar');
        if (sidebar) {
            sidebar.classList.toggle('show');
        }
    },

    checkAuth: function() {
        const token = window.Api ? window.Api.getToken() : localStorage.getItem('access_token');
        const isAdmin = localStorage.getItem('adminLoggedIn') === 'true';
        const isLoginPage = window.location.pathname.includes('login.html');

        if (!isLoginPage && (!token || !isAdmin)) {
            window.location.href = 'login.html';
            return false;
        }
        return true;
    },

    initAdminApp: function() {
        // Set active nav link based on current page
        const links = document.querySelectorAll('.admin-link');
        const currentPath = window.location.pathname;
        
        links.forEach(link => {
            const href = link.getAttribute('href');
            if (href && currentPath.endsWith(href)) {
                link.classList.add('active');
            }
        });

        // Toggle sidebar for mobile
        const toggler = document.getElementById('sidebarToggle');
        if (toggler) {
            toggler.addEventListener('click', () => this.toggleSidebar());
        }

        // Show logged-in admin name if element exists
        const userDataStr = localStorage.getItem('user_data');
        if (userDataStr) {
            try {
                const user = JSON.parse(userDataStr);
                const adminNameEl = document.getElementById('adminUserName');
                if (adminNameEl && user.full_name) {
                    adminNameEl.textContent = user.full_name;
                }
            } catch (e) {}
        }
    }
};

window.AppAdmin = AppAdmin;

document.addEventListener('DOMContentLoaded', () => {
    AppAdmin.initAdminApp();
});
