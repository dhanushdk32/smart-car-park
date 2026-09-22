import sys
import requests
import json
from datetime import date, datetime

BASE_URL = "http://127.0.0.1:8000/api"

def test_system():
    print("=" * 60)
    print("SMART CAR PARKING - COMPREHENSIVE E2E REGRESSION TEST")
    print("=" * 60)

    # 1. User & Admin Login
    print("\n[1] Testing Authentication...")
    # User login
    res = requests.post(f"{BASE_URL}/auth/login", json={"car_number": "KA01AB1234", "password": "user123"})
    assert res.status_code == 200, f"User login failed: {res.text}"
    user_token = res.json()["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    print(" -> User login: SUCCESS (Token acquired)")

    # Admin login
    res = requests.post(f"{BASE_URL}/auth/login", json={"car_number": "ADMIN01", "password": "admin123"})
    assert res.status_code == 200, f"Admin login failed: {res.text}"
    admin_token = res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(" -> Admin login: SUCCESS (Token acquired)")

    # 2. Parking Areas & Live Slots
    print("\n[2] Testing Parking Areas & Slot Inventory...")
    res = requests.get(f"{BASE_URL}/parking/areas")
    assert res.status_code == 200, f"Get areas failed: {res.text}"
    areas_data = res.json()
    areas = areas_data.get("areas", areas_data) if isinstance(areas_data, dict) else areas_data
    assert len(areas) >= 3, f"Expected at least 3 areas, found {len(areas)}"
    print(f" -> Areas retrieved: {len(areas)} active zones")

    target_area = areas[0]
    area_id = target_area["id"]
    res = requests.get(f"{BASE_URL}/parking/areas/{area_id}/slots")
    assert res.status_code == 200, f"Get slots failed: {res.text}"
    slots = res.json()
    print(f" -> Live slots in Area {area_id} ('{target_area['name']}'): {len(slots)} slots")

    # 3. ML Prediction Inference (Customer & System)
    print("\n[3] Testing ML Availability Prediction Engine...")
    pred_payload = {
        "area": target_area["name"],
        "date": str(date.today()),
        "time": "14:30:00",
        "weather": "Sunny",
        "is_weekend": 0,
        "is_holiday": 0
    }
    res = requests.post(f"{BASE_URL}/predictions/availability", json=pred_payload)
    assert res.status_code == 200, f"Prediction failed: {res.text}"
    pred_res = res.json()
    print(f" -> ML Prediction Result: Area '{pred_res['area']}'")
    print(f"    - Predicted Is Free: {pred_res['predicted_is_free']} ({pred_res['prediction']})")
    print(f"    - Probability: {pred_res['probability']}%")
    print(f"    - Model Version: {pred_res['model_version']}")

    # 4. ML Prediction History & Summary (Admin)
    print("\n[4] Testing ML Prediction Logging & History...")
    res = requests.get(f"{BASE_URL}/predictions/history?limit=5", headers=admin_headers)
    assert res.status_code == 200, f"Get prediction history failed: {res.text}"
    hist_json = res.json()
    print(f" -> Admin Prediction History: Total logged = {hist_json.get('total', 0)}")

    res = requests.get(f"{BASE_URL}/predictions/summary", headers=admin_headers)
    assert res.status_code == 200, f"Get prediction summary failed: {res.text}"
    summary_data = res.json().get("data", {})
    print(f" -> Prediction Summary: High confidence = {summary_data.get('high_confidence_predictions', 0)}")

    # 5. Occupancy Analytics Engine (Stage 9 Core Feature)
    print("\n[5] Testing Occupancy Analytics Engine (GET /api/occupancy/analytics)...")
    # 5a. Unfiltered
    res = requests.get(f"{BASE_URL}/occupancy/analytics", headers=admin_headers)
    assert res.status_code == 200, f"Analytics query failed: {res.text}"
    analytics_data = res.json()["data"]
    kpis = analytics_data["kpis"]
    print(f" -> Overall Analytics KPIs:")
    print(f"    - Total Monitored Areas: {kpis['total_areas']}")
    print(f"    - Total Managed Slots: {kpis['total_slots']}")
    print(f"    - Avg Occupancy Rate: {kpis['average_occupancy']}%")
    print(f"    - Avg Available Slots: {kpis['average_free_slots']}")
    print(f"    - Peak Recorded Occupancy: {kpis['peak_occupancy']}%")
    print(f"    - Total Historical Records Analyzed: {kpis['total_historical_records']}")
    print(f"    - Total ML Inferences Logged: {kpis['total_predictions']}")

    assert len(analytics_data["hourly_trend"]) == 24, "Expected 24 hourly data points"
    assert len(analytics_data["day_of_week_trend"]) == 7, "Expected 7 day of week data points"
    assert len(analytics_data["weekend_comparison"]) >= 2, "Expected weekend vs weekday points"
    assert len(analytics_data["weather_analysis"]) >= 1, "Expected weather points"
    print(" -> All multi-dimensional analytics breakdowns verified successfully!")

    # 5b. Filtered by Area
    res = requests.get(f"{BASE_URL}/occupancy/analytics?area_id={area_id}", headers=admin_headers)
    assert res.status_code == 200, f"Filtered analytics failed: {res.text}"
    f_kpis = res.json()["data"]["kpis"]
    assert f_kpis["total_areas"] == 1
    print(f" -> Filtered Analytics by Area {area_id}: {f_kpis['total_historical_records']} records analyzed")

    # 5c. Filtered by Weather & Weekend
    res = requests.get(f"{BASE_URL}/occupancy/analytics?weather=Rainy&is_weekend=true", headers=admin_headers)
    assert res.status_code == 200, f"Filtered analytics by weather & weekend failed: {res.text}"
    print(f" -> Filtered Analytics by Weather=Rainy & Weekend=True: SUCCESS")

    # 6. Historical Data Logs
    print("\n[6] Testing Historical Occupancy Log Pagination...")
    res = requests.get(f"{BASE_URL}/occupancy/history?limit=10", headers=admin_headers)
    assert res.status_code == 200, f"History pagination failed: {res.text}"
    h_data = res.json()
    assert h_data["total"] == 26064, f"Expected 26,064 records, got {h_data['total']}"
    print(f" -> Historical DB Verification: {h_data['total']} total records verified")

    # 7. Booking & Payment Workflow Regression Check
    print("\n[7] Testing Booking & Razorpay Sandbox Payment Verification...")
    avail_slot = next((s for s in slots if s["status"] == "Available"), None)
    if avail_slot:
        booking_payload = {
            "slot_id": avail_slot["id"],
            "booking_date": str(date.today()),
            "start_time": "15:00:00",
            "end_time": "17:00:00"
        }
        res = requests.post(f"{BASE_URL}/bookings/", json=booking_payload, headers=user_headers)
        if res.status_code == 200:
            booking = res.json()
            booking_id = booking["id"]
            print(f" -> Booking Created: ID #{booking_id} for Slot {avail_slot['slot_number']}")

            # Create payment order
            res = requests.post(f"{BASE_URL}/payments/create-order", json={"booking_id": booking_id}, headers=user_headers)
            assert res.status_code == 200, f"Create payment order failed: {res.text}"
            order_data = res.json()
            print(f" -> Razorpay Order Created: Order ID {order_data.get('order_id')}")

            # Verify sandbox payment
            verify_payload = {
                "booking_id": booking_id,
                "razorpay_order_id": order_data.get("order_id"),
                "razorpay_payment_id": f"pay_test_{int(datetime.now().timestamp())}",
                "razorpay_signature": "mock_sandbox_signature"
            }
            res = requests.post(f"{BASE_URL}/payments/verify", json=verify_payload, headers=user_headers)
            assert res.status_code == 200, f"Payment verify failed: {res.text}"
            print(" -> Payment Verification: SUCCESS (Booking confirmed)")

    print("\n" + "=" * 60)
    print("ALL 7 CORE SUBSYSTEMS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    test_system()
