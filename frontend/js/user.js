/**
 * User module for handling authentication and user specific interactions
 */

const AppUser = {
    handleLogin: async function(e) {
        if(e) e.preventDefault();
        
        const carNo = document.getElementById('loginCarNo').value;
        const password = document.getElementById('loginPassword').value;
        
        try {
            await window.Api.login(carNo, password);
            App.showToast('Login successful', 'success');
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000);
        } catch (error) {
            App.showToast(error.message, 'danger');
        }
    },

    handleRegister: async function(e) {
        if(e) e.preventDefault();

        const fullName = document.getElementById('fullName').value;
        const email = document.getElementById('email').value;
        const mobileNumber = document.getElementById('mobileNumber').value;
        const carNumber = document.getElementById('carNumberReg').value;
        const vehicleType = document.getElementById('vehicleType').value;
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        const confirmInput = document.getElementById('confirmPassword');

        if (password !== confirmPassword) {
            confirmInput.classList.add('is-invalid');
            return;
        } else {
            confirmInput.classList.remove('is-invalid');
        }

        if (fullName && email && mobileNumber && carNumber && vehicleType && password) {
            try {
                await window.Api.register(fullName, email, mobileNumber, carNumber, vehicleType, password);
                App.showToast('Success', 'Account created successfully. Please login.', 'success');
                setTimeout(() => {
                    window.location.href = 'login.html';
                }, 1500);
            } catch (error) {
                App.showToast(error.message, 'danger');
            }
        }
    },

    togglePasswordVisibility: function(inputId, iconElement) {
        const input = document.getElementById(inputId);
        const icon = iconElement.querySelector('i');
        
        if (input.type === 'password') {
            input.type = 'text';
            icon.classList.remove('bi-eye');
            icon.classList.add('bi-eye-slash');
        } else {
            input.type = 'password';
            icon.classList.remove('bi-eye-slash');
            icon.classList.add('bi-eye');
        }
    },

    checkAuth: function() {
        const isAuthPage = window.location.pathname.includes('login.html') || window.location.pathname.includes('register.html');
        const token = window.Api.getToken();
        
        if (!token && !isAuthPage && !window.location.pathname.endsWith('index.html')) {
            // Disabled strict auth redirect for easier testing during development
            // window.location.href = 'login.html';
        } else if (token && isAuthPage) {
            window.location.href = 'dashboard.html';
        }

        if (token) {
            const userDataStr = localStorage.getItem('user_data');
            if (userDataStr) {
                const userData = JSON.parse(userDataStr);
                const nameElements = document.querySelectorAll('.user-name-display');
                nameElements.forEach(el => el.textContent = userData.full_name);
                
                const carElements = document.querySelectorAll('.user-car-display');
                // car number not in token currently, could fetch profile here
            }
        }
    }
};

window.AppUser = AppUser;

// Protect routes
document.addEventListener('DOMContentLoaded', () => {
    AppUser.checkAuth();
});
