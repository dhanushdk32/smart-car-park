const mockData = {
    users: [
        { id: 1, name: 'John Doe', email: 'john@example.com', phone: '9876543210', carNumber: 'KA-01-AB-1234', vehicleType: 'Car', status: 'Active', registeredDate: '2026-01-15' },
        { id: 2, name: 'Jane Smith', email: 'jane@example.com', phone: '9876543211', carNumber: 'MH-12-CD-5678', vehicleType: 'SUV', status: 'Active', registeredDate: '2026-02-20' }
    ],
    parkingAreas: [
        { id: 'PA001', name: 'City Center', location: 'Downtown', totalSlots: 100, available: 45, occupied: 55, pricePerHour: 50, status: 'Active' },
        { id: 'PA002', name: 'Mall Parking', location: 'West End', totalSlots: 50, available: 32, occupied: 18, pricePerHour: 40, status: 'Active' },
        { id: 'PA003', name: 'Theatre Parking', location: 'East Side', totalSlots: 80, available: 12, occupied: 68, pricePerHour: 60, status: 'Active' }
    ],
    parkingSlots: {
        'PA002': [
            { id: 'A1', type: 'Regular', status: 'available' },
            { id: 'A2', type: 'Regular', status: 'occupied' },
            { id: 'A3', type: 'Regular', status: 'available' },
            { id: 'A4', type: 'Regular', status: 'available' },
            { id: 'A5', type: 'EV', status: 'occupied' },
            { id: 'B1', type: 'Regular', status: 'occupied' },
            { id: 'B2', type: 'Regular', status: 'reserved' },
            { id: 'B3', type: 'Regular', status: 'available' },
            { id: 'B4', type: 'Accessible', status: 'available' },
            { id: 'B5', type: 'EV', status: 'maintenance' },
            { id: 'C1', type: 'Regular', status: 'available' },
            { id: 'C2', type: 'Regular', status: 'available' },
            { id: 'C3', type: 'Regular', status: 'occupied' },
            { id: 'C4', type: 'Regular', status: 'available' },
            { id: 'C5', type: 'Regular', status: 'available' },
            { id: 'D1', type: 'Regular', status: 'available' },
            { id: 'D2', type: 'Regular', status: 'occupied' },
            { id: 'D3', type: 'Accessible', status: 'occupied' },
            { id: 'D4', type: 'EV', status: 'available' },
            { id: 'D5', type: 'EV', status: 'available' }
        ]
    },
    bookings: [
        { id: 'SP20260918001', userId: 1, carNumber: 'KA-01-AB-1234', areaId: 'PA002', areaName: 'Mall Parking', slot: 'A3', date: '2026-09-18', startTime: '17:00', endTime: '20:00', duration: 3, amount: 120, paymentStatus: 'Paid', status: 'Upcoming' },
        { id: 'SP20260917055', userId: 1, carNumber: 'KA-01-AB-1234', areaId: 'PA001', areaName: 'City Center', slot: 'C12', date: '2026-09-17', startTime: '10:00', endTime: '12:00', duration: 2, amount: 100, paymentStatus: 'Paid', status: 'Completed' }
    ],
    payments: [
        { paymentId: 'PAY001', bookingId: 'SP20260918001', customer: 'John Doe', amount: 120, method: 'UPI', status: 'Successful', date: '2026-09-18T14:30:00' }
    ],
    occupancy: {
        labels: ['8 AM', '10 AM', '12 PM', '2 PM', '4 PM', '6 PM', '8 PM'],
        data: [20, 45, 80, 85, 60, 95, 40]
    },
    predictions: {
        'PA002': {
            total: 50,
            predictedOccupied: 42,
            predictedFree: 8,
            occupancyRate: 84
        }
    }
};

// Export if using modules, or attach to window
window.mockData = mockData;
