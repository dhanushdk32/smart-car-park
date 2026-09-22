/**
 * Centralized API configuration for Smart Car Parking System
 */

const API_BASE_URL = "http://127.0.0.1:8000/api";

const Api = {
    getToken: function() {
        return localStorage.getItem('access_token');
    },

    setToken: function(token) {
        localStorage.setItem('access_token', token);
    },

    removeToken: function() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_data');
        localStorage.removeItem('adminLoggedIn');
    },

    getHeaders: function(isAuth = true) {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (isAuth) {
            const token = this.getToken();
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }
        return headers;
    },

    request: async function(endpoint, options = {}) {
        const isAuth = options.isAuth !== undefined ? options.isAuth : true;
        const headers = Object.assign({}, this.getHeaders(isAuth), options.headers || {});
        const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

        const config = {
            method: options.method || 'GET',
            headers: headers,
            ...options
        };

        if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
            config.body = JSON.stringify(options.body);
        }

        const response = await fetch(url, config);

        if (response.status === 401 || response.status === 403) {
            // Unauthorized or Forbidden
            if (window.location.pathname.includes('/admin/')) {
                if (!window.location.pathname.includes('login.html')) {
                    console.warn("Unauthorized admin access. Redirecting to login.");
                    localStorage.removeItem('adminLoggedIn');
                    window.location.href = 'login.html';
                }
            }
        }

        let data;
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        if (!response.ok) {
            const errorMsg = (data && data.detail) ? data.detail : (data && data.message ? data.message : 'API Request Failed');
            throw new Error(errorMsg);
        }

        return data;
    },

    // --- Auth APIs ---
    login: async function(car_number, password) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            isAuth: false,
            body: { car_number, password }
        });
        this.setToken(data.access_token);
        localStorage.setItem('user_data', JSON.stringify(data.user));
        if (data.user && data.user.role === 'admin') {
            localStorage.setItem('adminLoggedIn', 'true');
        }
        return data;
    },

    register: async function(userData) {
        return await this.request('/auth/register', {
            method: 'POST',
            isAuth: false,
            body: userData
        });
    },

    // --- Parking Public APIs ---
    getParkingAreas: async function() {
        return await this.request('/parking/areas', { isAuth: false });
    },

    getParkingArea: async function(id) {
        return await this.request(`/parking/areas/${id}`, { isAuth: false });
    },

    getParkingSlots: async function(areaId) {
        return await this.request(`/parking/areas/${areaId}/slots`, { isAuth: false });
    },

    // --- User Profile APIs ---
    getCurrentUser: async function() {
        return await this.request('/users/me');
    },

    // --- Booking APIs ---
    getAvailability: async function(areaId, date, startTime, duration) {
        return await this.request(`/parking/areas/${areaId}/availability?booking_date=${date}&start_time=${startTime}&duration=${duration}`, { isAuth: false });
    },

    createBooking: async function(bookingData) {
        return await this.request('/bookings', {
            method: 'POST',
            body: bookingData
        });
    },

    getBookings: async function(status = null) {
        let url = `/bookings`;
        if (status) url += `?status=${status}`;
        return await this.request(url);
    },

    cancelBooking: async function(bookingId) {
        return await this.request(`/bookings/${bookingId}/cancel`, {
            method: 'PUT'
        });
    },

    // --- Payment APIs ---
    createPaymentOrder: async function(bookingId) {
        return await this.request('/payments/create-order', {
            method: 'POST',
            body: { booking_id: bookingId }
        });
    },

    verifyPayment: async function(verificationData) {
        return await this.request('/payments/verify', {
            method: 'POST',
            body: verificationData
        });
    },

    getBookingPayment: async function(bookingId) {
        return await this.request(`/payments/booking/${bookingId}`);
    },

    // --- Admin APIs ---
    getAdminDashboard: async function() {
        return await this.request('/admin/dashboard');
    },

    getAdminUsers: async function(params = {}) {
        const q = new URLSearchParams(params).toString();
        return await this.request(`/admin/users${q ? '?' + q : ''}`);
    },

    getAdminUserDetails: async function(userId) {
        return await this.request(`/admin/users/${userId}`);
    },

    updateAdminUserStatus: async function(userId, isActive) {
        return await this.request(`/admin/users/${userId}/status?is_active=${isActive}`, {
            method: 'PUT'
        });
    },

    getAdminAreas: async function() {
        return await this.request('/admin/parking/areas');
    },

    createAdminArea: async function(areaData) {
        return await this.request('/admin/parking/areas', {
            method: 'POST',
            body: areaData
        });
    },

    updateAdminArea: async function(areaId, areaData) {
        return await this.request(`/admin/parking/areas/${areaId}`, {
            method: 'PUT',
            body: areaData
        });
    },

    deleteAdminArea: async function(areaId) {
        return await this.request(`/admin/parking/areas/${areaId}`, {
            method: 'DELETE'
        });
    },

    getAdminAreaSlots: async function(areaId) {
        return await this.request(`/admin/parking/areas/${areaId}/slots`);
    },

    createAdminSlot: async function(areaId, slotData) {
        return await this.request(`/admin/parking/areas/${areaId}/slots`, {
            method: 'POST',
            body: slotData
        });
    },

    updateAdminSlot: async function(slotId, slotData) {
        return await this.request(`/admin/parking/slots/${slotId}`, {
            method: 'PUT',
            body: slotData
        });
    },

    deleteAdminSlot: async function(slotId) {
        return await this.request(`/admin/parking/slots/${slotId}`, {
            method: 'DELETE'
        });
    },

    getAdminBookings: async function(params = {}) {
        const q = new URLSearchParams(params).toString();
        return await this.request(`/admin/bookings${q ? '?' + q : ''}`);
    },

    updateAdminBookingStatus: async function(bookingId, status) {
        return await this.request(`/admin/bookings/${bookingId}/status?status=${encodeURIComponent(status)}`, {
            method: 'PUT'
        });
    },

    getAdminPayments: async function(params = {}) {
        const q = new URLSearchParams(params).toString();
        return await this.request(`/admin/payments${q ? '?' + q : ''}`);
    },

    getAdminPaymentDetails: async function(paymentId) {
        return await this.request(`/admin/payments/${paymentId}`);
    },

    getAdminPaymentStats: async function() {
        return await this.request('/admin/payments/stats');
    },

    // --- Historical Occupancy APIs ---
    getOccupancyHistory: async function(params = {}) {
        const cleanParams = {};
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                cleanParams[key] = params[key];
            }
        });
        const q = new URLSearchParams(cleanParams).toString();
        return await this.request(`/occupancy/history${q ? '?' + q : ''}`);
    },

    getOccupancyRecord: async function(id) {
        return await this.request(`/occupancy/history/${id}`);
    },

    getOccupancySummary: async function(areaId = null, params = {}) {
        const cleanParams = {};
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                cleanParams[key] = params[key];
            }
        });
        const q = new URLSearchParams(cleanParams).toString();
        const url = areaId ? `/occupancy/summary/${areaId}${q ? '?' + q : ''}` : `/occupancy/summary${q ? '?' + q : ''}`;
        return await this.request(url);
    },

    getOccupancyTrends: async function(params = {}) {
        const cleanParams = {};
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                cleanParams[key] = params[key];
            }
        });
        const q = new URLSearchParams(cleanParams).toString();
        return await this.request(`/occupancy/trends${q ? '?' + q : ''}`);
    },

    getOccupancyComparison: async function() {
        return await this.request('/occupancy/comparison');
    },

    // --- ML Prediction APIs ---
    predictAvailability: async function(predictionData) {
        return await this.request('/predictions/availability', {
            method: 'POST',
            body: predictionData
        });
    },

    getPredictionHistory: async function(params = {}) {
        const cleanParams = {};
        Object.keys(params).forEach(key => {
            if (params[key] !== null && params[key] !== undefined && params[key] !== '') {
                cleanParams[key] = params[key];
            }
        });
        const q = new URLSearchParams(cleanParams).toString();
        return await this.request(`/predictions/history${q ? '?' + q : ''}`);
    },

    getPredictionRecord: async function(id) {
        return await this.request(`/predictions/${id}`);
    },

    getPredictionSummary: async function() {
        return await this.request('/predictions/summary');
    }
};

window.Api = Api;
