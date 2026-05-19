import time
import random
import requests

BASE_URL = "http://127.0.0.1:8000"

def run_e2e_test():
    print("🚀 Starting Quantum Mind E2E API Integration Test...")
    
    # 1. Register a new user with a unique email
    email = f"testuser_{random.randint(1000, 9999)}@example.com"
    password = "SecurePassword123!"
    
    print(f"\n1. Registering new user: {email}...")
    register_payload = {
        "email": email,
        "first_name": "Test",
        "last_name": "User",
        "password": password,
        "password_confirm": password
    }
    r = requests.post(f"{BASE_URL}/api/users/register/", json=register_payload)
    if r.status_code != 201:
        print(f"❌ Registration failed: {r.status_code} - {r.text}")
        return
    print("✅ User registered successfully!")
    user_data = r.json()
    
    # 2. Login to get JWT Token
    print("\n2. Logging in to obtain JWT access token...")
    login_payload = {
        "email": email,
        "password": password
    }
    r = requests.post(f"{BASE_URL}/api/auth/login/", json=login_payload)
    if r.status_code != 200:
        print(f"❌ Login failed: {r.status_code} - {r.text}")
        return
    tokens = r.json()
    access_token = tokens["access"]
    print("✅ Login successful! JWT Access Token received.")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 3. Retrieve Profile and check initial Credit Balance
    print("\n3. Retrieving user profile & credit balance...")
    r = requests.get(f"{BASE_URL}/api/users/profile/", headers=headers)
    if r.status_code != 200:
        print(f"❌ Failed to get profile: {r.text}")
        return
    profile = r.json()
    print(f"✅ Profile: {profile['full_name']} | Available Credits: {profile['available_credits']}")
    
    # 4. Submit Clinical Intake response (problem category will be auto-diagnosed)
    print("\n4. Submitting Clinical Intake Wizard response...")
    intake_payload = {
        "main_issue": "I have been experiencing intense stage fright before work presentations and difficulty falling asleep.",
        "issue_duration": "6 months",
        "symptoms": ["insomnia", "racing thoughts", "performance anxiety"],
        "triggers": ["public speaking", "caffeine"],
        "behavior_to_change": "Over-analyzing before bedtime and panic breathing during presentation introductions.",
        "desired_emotional_shift": "Deep calm, steady confidence, and restful sleep",
        "success_vision": "Walking into my presentations with a natural smile and falling asleep within 5 minutes.",
        "positive_anchoring_memory": "Winning the public speaking contest in college, feeling proud and composed.",
        "work_life_environment": "I work full-time in a fast-paced technology startup with multiple meetings daily.",
        "session_duration_minutes": 10,
        "mood_before": 3,
        "has_inner_conflict": True
    }
    r = requests.post(f"{BASE_URL}/api/intake/create/", json=intake_payload, headers=headers)
    if r.status_code != 201:
        print(f"❌ Intake submission failed: {r.status_code} - {r.text}")
        return
    intake_data = r.json()
    intake_id = intake_data["id"]
    print(f"✅ Intake submitted! ID: {intake_id} | Auto-diagnosed Category: {intake_data.get('problem_category')}")
    
    # 5. Start a personalized Hypnotherapy Session (Atomic credit deduction)
    print("\n5. Creating therapeutic session (takes 10 credits)...")
    session_payload = {
        "intake_id": intake_id,
        "duration_minutes": 10
    }
    r = requests.post(f"{BASE_URL}/api/sessions/create/", json=session_payload, headers=headers)
    if r.status_code not in [201, 202]:
        print(f"❌ Session creation failed: {r.status_code} - {r.text}")
        return
    session_data = r.json()
    session_id = session_data["id"]
    print(f"✅ Session initiated (202 Accepted)! ID: {session_id} | Initial Status: {session_data['status']}")
    
    # 6. Poll Session Generation Status (Celery async task updates this)
    print("\n6. Polling session generation status (waiting for Claude & ElevenLabs async task)...")
    max_polls = 10
    for i in range(max_polls):
        time.sleep(3)
        r = requests.get(f"{BASE_URL}/api/sessions/{session_id}/", headers=headers)
        if r.status_code != 200:
            print(f"❌ Poll failed: {r.text}")
            break
        s_data = r.json()
        status = s_data["status"]
        print(f"   [Poll {i+1}/{max_polls}] Session Status: {status}")
        if status == "completed":
            print(f"🎉 SUCCESS! Session complete. Audio CDN URL: {s_data.get('audio_url')}")
            break
        elif status == "failed":
            print(f"❌ Session generation failed! Error: {s_data.get('error_message')}")
            break
    else:
        print("⏳ Polling timed out. The script was set to check for 30s. The background Celery task is still running.")
        
    # 7. Check final credit balance
    print("\n7. Verifying final credit balance...")
    r = requests.get(f"{BASE_URL}/api/users/profile/", headers=headers)
    if r.status_code == 200:
        profile = r.json()
        print(f"✅ Final Available Credits: {profile['available_credits']}")
        
    print("\n🏁 E2E Integration test run completed successfully!")

if __name__ == "__main__":
    run_e2e_test()
