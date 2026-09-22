/**
 * Chart rendering logic for admin dashboard using Chart.js
 */

const AppCharts = {
    colors: {
        primary: '#2563eb',
        success: '#10b981',
        warning: '#f59e0b',
        danger: '#ef4444',
        info: '#0ea5e9',
        purple: '#8b5cf6',
        gray: '#e2e8f0'
    },

    initDashboardCharts: function(liveData = null) {
        this.renderOccupancyTrend(liveData);
        this.renderRevenueChart(liveData ? liveData.revenue_trend : null);
        this.renderAreaComparison(liveData ? liveData.areas_overview : null);
    },

    initAnalyticsCharts: function() {
        this.renderOccupancyTrend();
        this.renderWeeklyOccupancy();
        this.renderAreaComparison();
        this.renderRevenueChart();
    },

    renderOccupancyTrend: function() {
        const ctx = document.getElementById('occupancyChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: window.mockData.occupancy.labels,
                datasets: [{
                    label: 'Occupied Slots',
                    data: window.mockData.occupancy.data,
                    borderColor: this.colors.primary,
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true, max: 100 }
                }
            }
        });
    },

    renderRevenueChart: function(liveTrend = null) {
        const ctx = document.getElementById('revenueChart');
        if (!ctx) return;

        let labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
        let data = [0, 0, 0, 0, 0, 0, 0];

        if (liveTrend && Array.isArray(liveTrend) && liveTrend.length > 0) {
            labels = liveTrend.map(item => item.date);
            data = liveTrend.map(item => item.amount);
        }

        if (ctx._chartInstance) {
            ctx._chartInstance.destroy();
        }

        ctx._chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Revenue (₹)',
                    data: data,
                    backgroundColor: this.colors.success,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                }
            }
        });
    },

    renderAreaComparison: function(liveAreas = null) {
        const ctx = document.getElementById('areaComparisonChart');
        if (!ctx) return;

        let labels = ['Area A', 'Area B', 'Area C'];
        let data = [10, 20, 15];

        if (liveAreas && Array.isArray(liveAreas) && liveAreas.length > 0) {
            labels = liveAreas.map(a => a.name);
            data = liveAreas.map(a => a.occupied || 0);
        } else if (window.mockData && window.mockData.parkingAreas) {
            labels = window.mockData.parkingAreas.map(a => a.name);
            data = window.mockData.parkingAreas.map(a => a.occupied);
        }

        if (ctx._chartInstance) {
            ctx._chartInstance.destroy();
        }

        ctx._chartInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [this.colors.primary, this.colors.info, this.colors.purple, this.colors.warning, this.colors.success],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    },

    renderWeeklyOccupancy: function() {
        const ctx = document.getElementById('weeklyOccupancyChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Average Occupancy %',
                    data: [45, 52, 58, 65, 85, 95, 80],
                    backgroundColor: this.colors.purple,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100 }
                }
            }
        });
    }
};

window.AppCharts = AppCharts;
