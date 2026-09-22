/**
 * Payment module for handling frontend payment simulation
 */

const AppPayment = {
    bookingData: null,

    initPaymentPage: function() {
        const dataStr = sessionStorage.getItem('pendingBooking');
        if (!dataStr) {
            window.location.href = 'parking.html';
            return;
        }

        this.bookingData = JSON.parse(dataStr);
        
        // Populate UI
        document.getElementById('pay-area').textContent = this.bookingData.areaName;
        document.getElementById('pay-slot').textContent = this.bookingData.slotId;
        
        const formattedDate = new Date(this.bookingData.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
        
        // Calculate end time roughly for display
        let [hours, minutes] = this.bookingData.time.split(':');
        let endHours = (parseInt(hours) + parseInt(this.bookingData.duration)) % 24;
        
        function formatTime(h, m) {
            let period = 'AM';
            if (h >= 12) { period = 'PM'; if (h > 12) h -= 12; }
            if (h == 0) h = 12;
            return `${String(h).padStart(2, '0')}:${m} ${period}`;
        }

        document.getElementById('pay-datetime').textContent = `${formattedDate}, ${formatTime(hours, minutes)} - ${formatTime(endHours, minutes)}`;
        
        const totalHtml = `₹${this.bookingData.total.toFixed(2)}`;
        document.getElementById('pay-total').textContent = totalHtml;
        document.getElementById('btn-pay-text').textContent = `Pay ${totalHtml}`;
    },

    selectMethod: function(methodId) {
        // Handle UI selection
        const methods = ['method-upi', 'method-card', 'method-net'];
        methods.forEach(m => {
            const el = document.getElementById(m);
            if(el) {
                el.classList.remove('border-primary', 'bg-primary', 'bg-opacity-10');
                el.querySelector('.form-check-input').checked = false;
            }
        });

        const selectedEl = document.getElementById(methodId);
        if(selectedEl) {
            selectedEl.classList.add('border-primary', 'bg-primary', 'bg-opacity-10');
            selectedEl.querySelector('.form-check-input').checked = true;
        }

        // Show relevant form
        document.getElementById('form-upi').classList.add('d-none');
        document.getElementById('form-card').classList.add('d-none');
        document.getElementById('form-net').classList.add('d-none');

        if (methodId === 'method-upi') document.getElementById('form-upi').classList.remove('d-none');
        if (methodId === 'method-card') document.getElementById('form-card').classList.remove('d-none');
        if (methodId === 'method-net') document.getElementById('form-net').classList.remove('d-none');
    },

    processPayment: function() {
        const btn = document.getElementById('btn-pay');
        const originalText = btn.innerHTML;
        
        // Simulate processing
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
        btn.disabled = true;

        setTimeout(() => {
            // Generate mock booking ID
            const dateStr = new Date().toISOString().slice(0,10).replace(/-/g, '');
            const randomNum = Math.floor(Math.random() * 900) + 100;
            const bookingId = `SP${dateStr}${randomNum}`;

            this.bookingData.bookingId = bookingId;
            sessionStorage.setItem('confirmedBooking', JSON.stringify(this.bookingData));
            sessionStorage.removeItem('pendingBooking');

            window.location.href = 'confirmation.html';
        }, 2000);
    },

    initConfirmationPage: function() {
        const dataStr = sessionStorage.getItem('confirmedBooking');
        if (!dataStr) {
            window.location.href = 'dashboard.html';
            return;
        }

        const data = JSON.parse(dataStr);
        
        document.getElementById('conf-booking-id').textContent = data.bookingId;
        document.getElementById('conf-area').textContent = data.areaName;
        document.getElementById('conf-slot').textContent = data.slotId;
        
        const formattedDate = new Date(data.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
        document.getElementById('conf-date').textContent = formattedDate;

        let [hours, minutes] = data.time.split(':');
        let endHours = (parseInt(hours) + parseInt(data.duration)) % 24;
        
        function formatTime(h, m) {
            let period = 'AM';
            if (h >= 12) { period = 'PM'; if (h > 12) h -= 12; }
            if (h == 0) h = 12;
            return `${String(h).padStart(2, '0')}:${m} ${period}`;
        }
        
        document.getElementById('conf-time').textContent = `${formatTime(hours, minutes)} - ${formatTime(endHours, minutes)}`;
        document.getElementById('conf-amount').textContent = `₹${data.total.toFixed(2)}`;
    }
};

window.AppPayment = AppPayment;
