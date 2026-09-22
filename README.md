# Smart Car Parking Management System with Machine Learning-Based Free Slot Prediction and Analysis

A production-grade, portfolio-ready smart parking management platform combining real-time parking spot reservations, automated Razorpay sandbox payments, historical occupancy analytics, and Machine Learning availability forecasting.

---

## 🏛️ System Architecture

```mermaid
graph TD
    subgraph Client Layer
        A1[Customer Web Portal] -->|HTTP / JSON| API[FastAPI Gateway]
        A2[Admin Management Portal] -->|HTTP / Bearer JWT| API
    end

    subgraph Backend Services
        API --> B1[Auth & JWT Security]
        API --> B2[Live Slot & Booking Engine]
        API --> B3[Razorpay Payment Verification]
        API --> B4[Occupancy Analytics Engine]
        API --> B5[ML Prediction Inference Service]
    end

    subgraph Data & ML Layer
        B1 & B2 & B3 & B4 & B5 --> DB[(MySQL Database)]
        B5 --> ML[Gradient Boosting Classifier<br/>parking_availability_model.joblib]
        DB --> HIST[(26,064 Historical Records<br/>parking_occupancy)]
    end
```

### 🎯 Key Architectural Principle: Live Slots vs ML Predictions
- **Live Slot Availability (`parking_slots` Table)**: Real-time, atomic slot allocation guaranteeing that reserved slots cannot be double-booked. Governs actual physical check-ins, spot allocations (e.g., Slot A-01), and active bookings.
- **Machine Learning Area Prediction (`parking_availability_model.joblib`)**: Predictive classification engine that outputs probability scores of finding free parking for any given area, date, hour, day of week, and weather condition based on historical patterns.

---

## ✨ Features

### 👤 Customer Experience
- **Interactive Parking Navigation**: Browse monitored parking areas (City Center, Mall, Theatre) with live capacity badges and pricing.
- **Dynamic Slot Selector**: Visual slot grid categorized by spot types (Regular, EV Charging, Accessible) with real-time status indicators (Available, Occupied, Reserved, Maintenance).
- **Online Booking & Razorpay Sandbox Payments**: Seamless checkout with Razorpay sandbox integration, automated order creation, and cryptographic signature verification.
- **Digital Parking Pass & QR Code**: Immediate booking confirmation with parking pass details and ticket QR code.
- **Customer ML Availability Predictor**: Forecast parking likelihood before driving based on target arrival time, weather, and day characteristics.
- **Booking History**: Real-time log of active, completed, and cancelled reservations.

### 🛡️ Admin Management & Analytics
- **Executive Operations Dashboard**: High-level telemetry of live slot utilization, active bookings, revenue, and recent alerts.
- **Parking Area & Slot CRUD**: Full administrative control to create, edit, activate/deactivate areas and manage individual slot statuses.
- **Advanced Occupancy Analytics (`analytics.html`)**:
  - Direct SQL aggregation over **26,064 historical occupancy records**.
  - **8 Key Performance Indicators (KPIs)**: Total Areas, Total Monitored Slots, Facility Average Occupancy, Average Available Free Slots, Peak Occupancy, Lowest Baseline Occupancy, Total Records Analyzed, and ML Prediction Queries Logged.
  - **Interactive Multi-Filter Bar**: Area, Date Range (Start/End), Day of Week, Weather condition, Weekend flag, and Holiday flag.
  - **Visualizations (Chart.js)**: 24-hour hourly trend line, area comparison, day-of-week demand curve, weekend vs weekday doughnut, and weather impact distribution.
  - **Bottleneck Detection**: Automatic flagging of peak congestion hours (&ge; 80% occupancy).
- **ML Model Performance Dashboard (`model-performance.html`)**:
  - Detailed offline test evaluation metrics: **Accuracy 92.54%**, **Precision 94.32%**, **Recall 97.53%**, **F1-Score 95.90%**.
  - Full **Confusion Matrix** on holdout test set (5,213 records).
  - Feature transformation specifications and preprocessing pipeline documentation.
- **ML Prediction History (`predictions.html`)**: Detailed log of all user/admin predictive inferences stored in MySQL.
- **Bookings & Payment Auditing**: Real-time management of check-ins, check-outs, payment receipts, and refund statuses.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | HTML5, CSS3, Vanilla JavaScript, Bootstrap 5.3, Bootstrap Icons, Chart.js, Razorpay Checkout JS |
| **Backend** | Python 3.10+, FastAPI, Uvicorn, SQLAlchemy ORM, Pydantic v2, PyJWT, Passlib (bcrypt) |
| **Machine Learning** | Scikit-learn (GradientBoostingClassifier), Joblib, Pandas, NumPy |
| **Database** | MySQL 8.0+ via PyMySQL connector |
| **Security** | Role-Based Access Control (RBAC), Password Hashing, JWT Bearer Tokens, Razorpay HMAC-SHA256 signature verification |

---

## 🚀 Setup & Installation Guide

### 1. Prerequisites
- Python 3.10 or higher
- MySQL 8.0 or higher
- Git

### 2. Database Configuration
Open MySQL CLI or MySQL Workbench and create the database:
```sql
CREATE DATABASE IF NOT EXISTS smart_car_park CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Backend Setup
1. Open terminal and navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   ```
3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   Copy `.env.example` to `.env` and configure your MySQL credentials:
   ```env
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/smart_car_park
   SECRET_KEY=your_super_secret_jwt_key_here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   RAZORPAY_KEY_ID=rzp_test_your_key_id
   RAZORPAY_KEY_SECRET=your_razorpay_secret
   ```
5. Seed initial areas, slots, and default users:
   ```bash
   python seed.py
   ```
6. Import historical occupancy data (26,064 records):
   ```bash
   python -m scripts.import_historical_data
   ```

### 4. Run the Backend Server
```bash
uvicorn app.main:app --port 8000 --reload
```
The FastAPI interactive documentation will be available at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 5. Launch the Frontend
You can serve the `frontend/` directory using Python's built-in HTTP server or VS Code Live Server:
```bash
cd ../frontend
python -m http.server 5500
```
Then open your browser at:
- **Customer Portal**: [http://localhost:5500/user/parking.html](http://localhost:5500/user/parking.html)
- **Admin Portal**: [http://localhost:5500/admin/login.html](http://localhost:5500/admin/login.html)

---

## 🔑 Default Credentials

| Portal | Username / Car Number | Password | Role |
|---|---|---|---|
| **Admin Portal** | `ADMIN01` | `admin123` | Administrator |
| **Customer Portal** | `KA01AB1234` | `user123` | Registered Driver |

---

## 📊 Machine Learning Model Specifications

- **Algorithm**: `GradientBoostingClassifier` (scikit-learn)
- **Artifact**: `backend/app/ml/parking_availability_model.joblib`
- **Features Used**:
  - `area` (Categorical, OneHotEncoded)
  - `hour` (0–23, Integer)
  - `minute` (0–59, Integer)
  - `day_number` (1–31, Integer)
  - `day_of_week` (Monday–Sunday, Categorical)
  - `month` (January–December, Categorical)
  - `is_weekend` (0/1, Boolean)
  - `is_holiday` (0/1, Boolean)
  - `weather` (Sunny, Cloudy, Rainy, Categorical)
- **Target**: `is_free` (1 = At least one available slot, 0 = Full capacity)
- **Test Performance (Holdout Set N = 5,213)**:
  - **Accuracy**: 92.54%
  - **Precision (Class 1)**: 94.32%
  - **Recall (Class 1)**: 97.53%
  - **F1-Score (Class 1)**: 95.90%
- **Confusion Matrix**:
  ```
                 Predicted Full (0)    Predicted Available (1)
  Actual Full (0)        276 (TN)               274 (FP)
  Actual Avail (1)       115 (FN)             4,548 (TP)
  ```

---

## 🔒 Security Best Practices
- Passwords hashed using industry-standard **bcrypt**.
- Endpoints protected with **JWT Bearer Authentication** and strict role enforcement (`admin` vs `user`).
- Razorpay payment integrity validated via server-side **HMAC-SHA256** checksum verification.
- Sensitive environment configurations isolated in `.env` (excluded via `.gitignore`).

---

## 📄 License
This project is open-source and intended for educational and portfolio demonstration purposes.
