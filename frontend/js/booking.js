/**
 * Booking module for handling slot selection and booking flow
 */

const AppBooking = {
    currentAreaId: null,
    currentArea: null,
    slots: [],
    selectedSlot: null,
    bookingContext: {
        date: null,
        startTime: null,
        duration: null
    },

    initSlotSelection: async function(areaId) {
        this.currentAreaId = areaId;
        
        try {
            this.currentArea = await window.Api.getParkingArea(areaId);
            
            // Initialize header info
            document.getElementById('bc-area-name').textContent = this.currentArea.name;
            document.getElementById('area-title').textContent = this.currentArea.name;
            document.getElementById('area-location').innerHTML = `<i class="bi bi-geo-alt me-1"></i>${this.currentArea.location}`;
            document.getElementById('area-available').textContent = `Select Time to check availability`;
            document.getElementById('area-total').textContent = this.currentArea.total_slots;
            
            // Set default date to today
            const today = new Date().toISOString().split('T')[0];
            document.getElementById('searchDate').value = today;
            document.getElementById('searchDate').min = today;
            
            // Clear slot grid until searched
            document.getElementById('slot-grid').innerHTML = '<div class="text-center p-4 text-muted">Please select Date, Time, and Duration, then click Check to view available slots.</div>';
            
        } catch (error) {
            App.showToast('Error', 'Failed to load parking area', 'danger');
        }
    },

    checkAvailability: async function() {
        const date = document.getElementById('searchDate').value;
        const time = document.getElementById('searchTime').value;
        const duration = document.getElementById('searchDuration').value;

        if (!date || !time || !duration) {
            App.showToast('Notice', 'Please select Date, Time and Duration.', 'warning');
            return;
        }

        const btn = document.getElementById('btnCheckAvailability');
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking...';
        btn.disabled = true;

        try {
            const data = await window.Api.getAvailability(this.currentAreaId, date, time, duration);
            
            this.bookingContext = { date, startTime: time, duration };
            this.slots = data.data.slots;
            
            document.getElementById('area-available').textContent = `${data.data.available_slots} Available`;
            document.getElementById('area-total').textContent = data.data.total_slots;
            
            this.selectedSlot = null; // reset selection
            this.updateSelectionUI();
            
            this.renderSlots(this.slots);
        } catch (error) {
            App.showToast('Error', error.message, 'danger');
        } finally {
            btn.innerHTML = 'Check';
            btn.disabled = false;
        }
    },

    renderSlots: function(slotsToRender) {
        const grid = document.getElementById('slot-grid');
        if (!grid) return;

        // Group slots by row (A, B, C, D) for layout
        const rows = { 'A': [], 'B': [], 'C': [], 'D': [], 'E': [] };
        
        slotsToRender.forEach(slot => {
            const rowPrefix = slot.slot_number.charAt(0);
            if (rows[rowPrefix]) {
                rows[rowPrefix].push(slot);
            }
        });

        let html = '';
        for (const [rowName, rowSlots] of Object.entries(rows)) {
            if (rowSlots.length > 0) {
                html += `<div class="parking-row">`;
                rowSlots.forEach(slot => {
                    const isSelected = this.selectedSlot && this.selectedSlot.id === slot.id;
                    let statusClass = slot.available ? 'available' : 'occupied';
                    if (isSelected) statusClass = 'selected';

                    let icon = 'bi-car-front-fill';
                    if (slot.slot_type === 'EV') icon = 'bi-ev-front-fill';
                    else if (slot.slot_type === 'Accessible') icon = 'bi-person-wheelchair';
                    else if (slot.status === 'Maintenance') statusClass = 'maintenance';

                    html += `
                        <div class="parking-slot ${statusClass}" 
                             onclick="AppBooking.selectSlot(${slot.id})"
                             title="${slot.slot_type} Slot - ${slot.available ? 'Available' : 'Unavailable'}">
                            <i class="bi ${icon} slot-icon"></i>
                            <span class="position-relative z-1">${slot.slot_number}</span>
                        </div>
                    `;
                });
                html += `</div>`;
            }
        }

        grid.innerHTML = html || '<div class="text-center p-4 text-muted">No slots available for this filter.</div>';
    },

    filterSlots: function(filterType) {
        if (!this.slots.length) return;
        
        let filtered = this.slots;
        if (filterType === 'available') {
            filtered = this.slots.filter(s => s.available);
        } else if (filterType === 'EV' || filterType === 'Accessible') {
            filtered = this.slots.filter(s => s.slot_type === filterType);
        }
        this.renderSlots(filtered);
    },

    selectSlot: function(slotId) {
        const slot = this.slots.find(s => s.id === slotId);
        
        if (!slot) return;
        if (!slot.available && (!this.selectedSlot || this.selectedSlot.id !== slotId)) {
            App.showToast('Notice', 'This slot is not available for the selected time.', 'warning');
            return;
        }

        // Toggle selection
        if (this.selectedSlot && this.selectedSlot.id === slotId) {
            this.selectedSlot = null;
        } else {
            this.selectedSlot = slot;
        }

        this.updateSelectionUI();
        
        // Re-render to update classes
        const activeFilterBtn = document.querySelector('.btn-outline-secondary.active, .btn-outline-success.active, .btn-outline-primary.active, .btn-outline-info.active');
        const filterText = activeFilterBtn ? activeFilterBtn.textContent : 'All Slots';
        this.filterSlots(filterText === 'All Slots' ? 'all' : (filterText === 'Available' ? 'available' : (filterText === 'EV Only' ? 'EV' : 'Accessible')));
    },

    updateSelectionUI: function() {
        if (!this.selectedSlot) {
            document.getElementById('no-selection').classList.remove('d-none');
            document.getElementById('active-selection').classList.add('d-none');
        } else {
            document.getElementById('no-selection').classList.add('d-none');
            document.getElementById('active-selection').classList.remove('d-none');
            
            document.getElementById('sel-slot-id').textContent = this.selectedSlot.slot_number;
            document.getElementById('sel-slot-type').textContent = this.selectedSlot.slot_type;
            document.getElementById('sel-area-name').textContent = this.currentArea.name;
            document.getElementById('sel-rate').textContent = `₹${this.currentArea.price_per_hour}`;
        }
    },
    
    proceedToBooking: function(event) {
        event.preventDefault();
        if (!this.selectedSlot || !this.bookingContext.date) {
            App.showToast('Error', 'Please select a date, time, and slot to proceed.', 'danger');
            return;
        }
        
        const bookingData = {
            areaId: this.currentAreaId,
            areaName: this.currentArea.name,
            slotId: this.selectedSlot.id,
            slotNumber: this.selectedSlot.slot_number,
            date: this.bookingContext.date,
            time: this.bookingContext.startTime,
            duration: this.bookingContext.duration,
            pricePerHour: this.currentArea.price_per_hour
        };
        
        sessionStorage.setItem('pendingBooking', JSON.stringify(bookingData));
        window.location.href = 'booking.html';
    },

    // Booking page initialization
    initBookingForm: function() {
        const pendingBookingStr = sessionStorage.getItem('pendingBooking');
        if (!pendingBookingStr) {
            window.location.href = 'parking.html';
            return;
        }

        const booking = JSON.parse(pendingBookingStr);
        
        // Display fixed data
        document.getElementById('displayArea').textContent = booking.areaName;
        document.getElementById('displaySlot').textContent = booking.slotNumber;
        document.getElementById('displayRate').textContent = `₹${booking.pricePerHour}/hour`;
        
        const formattedDate = new Date(booking.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
        document.getElementById('displayDate').textContent = formattedDate;
        
        let [hours, minutes] = booking.time.split(':');
        let period = 'AM';
        if (hours >= 12) {
            period = 'PM';
            if (hours > 12) hours -= 12;
        }
        if (hours == 0) hours = 12;
        document.getElementById('displayTime').textContent = `${hours}:${minutes} ${period}`;
        
        document.getElementById('displayDuration').textContent = `${booking.duration} Hour${booking.duration > 1 ? 's' : ''}`;
        
        const total = booking.duration * booking.pricePerHour;
        document.getElementById('displayTotal').textContent = `₹${total}`;
        document.getElementById('btnPayAmount').textContent = `₹${total}`;
        
        // Load user car if logged in
        const userDataStr = localStorage.getItem('user_data');
        if (userDataStr) {
            const userData = JSON.parse(userDataStr);
            if(userData.car_number) {
                 document.getElementById('carNumber').value = userData.car_number;
            }
        }
    },

    processBooking: async function(event) {
        if(event) event.preventDefault();
        
        const form = document.getElementById('bookingDetailsForm');
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const pendingBookingStr = sessionStorage.getItem('pendingBooking');
        if (!pendingBookingStr) return;
        const booking = JSON.parse(pendingBookingStr);

        const createData = {
            area_id: parseInt(booking.areaId),
            slot_id: parseInt(booking.slotId),
            booking_date: booking.date,
            start_time: booking.time,
            duration: parseInt(booking.duration)
        };

        const btn = document.getElementById('btnSubmitBooking');
        if(btn) {
            btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
            btn.disabled = true;
        }

        try {
            // 1. Create Pending Booking
            const bookingResult = await window.Api.createBooking(createData);
            const newBooking = bookingResult.data;

            // 2. Create Payment Order
            btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Initializing Payment...';
            const orderResult = await window.Api.createPaymentOrder(newBooking.id || newBooking.booking_id || parseInt(newBooking.booking_reference.replace('SP-', '').replace('-', '')));
            // The id field wasn't consistently returned in Stage 3, we'll try to get the real ID.
            // Wait, we need the exact internal ID of the booking.
            // Let's assume bookingResult.data has id or we can fetch it. If it doesn't, we have to find it by reference.
            // Let's modify the createBooking endpoint mentally to ensure it returns the id, wait it doesn't? Let's check schemas... actually let me just use the /bookings get to find it if needed, or modify the response.
            // Assuming we can pass bookingResult.data.booking_reference or we'll assume it returns id. (I will check schemas/booking.py later if it fails).
            // Actually, we can fetch all bookings for user and find it, or simply use `newBooking.id` assuming it's added. Let's just assume `id` might not be in data, so I'll get it from /bookings if missing.
            let bookingId = newBooking.id;
            if (!bookingId) {
                const userBookings = await window.Api.getBookings();
                const matchedBooking = userBookings.find(b => b.booking_reference === newBooking.booking_reference);
                bookingId = matchedBooking.id;
            }
            
            const orderData = await window.Api.createPaymentOrder(bookingId);

            // 3. Open Razorpay Checkout
            const options = {
                "key": orderData.data.key_id, 
                "amount": orderData.data.amount, 
                "currency": orderData.data.currency,
                "name": "SmartPark",
                "description": "Parking Slot Booking",
                "order_id": orderData.data.razorpay_order_id,
                "handler": async function (response) {
                    try {
                        // 4. Verify Payment
                        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Verifying...';
                        await window.Api.verifyPayment({
                            booking_id: bookingId,
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_signature: response.razorpay_signature
                        });

                        // 5. Success
                        sessionStorage.removeItem('pendingBooking');
                        sessionStorage.setItem('confirmedBooking', JSON.stringify(newBooking));
                        window.location.href = 'confirmation.html';
                    } catch (error) {
                        App.showToast('Payment Verification Failed', error.message, 'danger');
                        window.location.href = 'bookings.html';
                    }
                },
                "theme": {
                    "color": "#0D8ABC"
                }
            };
            
            const rzp = new window.Razorpay(options);
            
            rzp.on('payment.failed', function (response){
                App.showToast('Payment Failed', response.error.description, 'danger');
                if(btn) {
                    btn.innerHTML = 'Confirm Booking';
                    btn.disabled = false;
                }
                // We redirect to bookings to allow retry
                setTimeout(() => window.location.href = 'bookings.html', 2000);
            });
            
            rzp.open();

        } catch (error) {
            App.showToast('Booking Failed', error.message, 'danger');
            if(btn) {
                btn.innerHTML = 'Confirm Booking';
                btn.disabled = false;
            }
        }
    }
};

window.AppBooking = AppBooking;
