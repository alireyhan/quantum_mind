# 📖 Quantum Mind — API Collection Reference

This document serves as the master API directory for the **Quantum Mind** backend. All endpoints are fully registered, functional, and backed by your PostgreSQL database and Celery worker infrastructure.

---

## 🧭 Table of Contents
1. [Headers & Global Settings](#-headers--global-settings)
2. [🔐 Authentication & User Registration](#-1-authentication--user-registration)
3. [📋 Clinical Intake Wizard](#-2-clinical-intake-wizard)
4. [🎧 Asynchronous Therapy Sessions](#-3-asynchronous-therapy-sessions)
5. [💎 Credit Ledger System](#-4-credit-ledger-system)
6. [📈 Mood & Adaptive AI Feedback](#-5-mood--adaptive-ai-feedback)
7. [🗺️ Multi-Day Therapeutic Programs](#-6-multi-day-therapeutic-programs)

---

## ⚙️ Headers & Global Settings

* **Base URL**: `http://localhost:8000/api` (for local development)
* **Default Request Format**: `Content-Type: application/json`
* **Authorization Scheme**: All protected routes require a JSON Web Token (JWT) sent via the `Authorization` header:
  ```http
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
  ```

---

## 🔐 1. Authentication & User Registration

### 1.1 User Registration
* **Endpoint**: `POST /users/register/`
* **Auth**: Public (None)
* **Description**: Registers a new user. Automatically credits them with 10 free minutes.
* **Request Body**:
  ```json
  {
    "email": "jane.doe@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "password": "SecurePassword123!",
    "password_confirm": "SecurePassword123!"
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "id": 12,
    "email": "jane.doe@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "full_name": "Jane Doe",
    "date_joined": "2026-05-18T02:00:00Z",
    "is_premium": false,
    "premium_expires_at": null,
    "free_minutes_used": 0,
    "purchased_credits": 0,
    "available_credits": 10,
    "free_minutes_remaining": 10
  }
  ```
* **Response (400 Bad Request — Passwords Do Not Match)**:
  ```json
  {
    "password_confirm": [
      "Passwords do not match."
    ]
  }
  ```

### 1.2 User Login (Obtain JWT)
* **Endpoint**: `POST /auth/login/`
* **Auth**: Public (None)
* **Description**: Verifies credentials and returns access and refresh JWT tokens.
* **Request Body**:
  ```json
  {
    "email": "jane.doe@example.com",
    "password": "SecurePassword123!"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIs...",
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwi..."
  }
  ```
* **Response (401 Unauthorized)**:
  ```json
  {
    "detail": "No active account found with the given credentials"
  }
  ```

### 1.3 Refresh Token
* **Endpoint**: `POST /auth/refresh/`
* **Auth**: Public (None)
* **Description**: Exchanges a valid refresh token for a brand new access token.
* **Request Body**:
  ```json
  {
    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIs..."
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwi..."
  }
  ```

### 1.4 Get Profile
* **Endpoint**: `GET /users/profile/`
* **Auth**: Protected (Bearer)
* **Description**: Returns detailed current user account and credit status.
* **Response (200 OK)**:
  ```json
  {
    "id": 12,
    "email": "jane.doe@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "full_name": "Jane Doe",
    "date_joined": "2026-05-18T02:00:00Z",
    "is_premium": false,
    "premium_expires_at": null,
    "free_minutes_used": 0,
    "purchased_credits": 0,
    "available_credits": 10,
    "free_minutes_remaining": 10
  }
  ```

### 1.5 Update Profile
* **Endpoint**: `PATCH /users/profile/`
* **Auth**: Protected (Bearer)
* **Description**: Modifies first and last name fields.
* **Request Body**:
  ```json
  {
    "first_name": "Janet",
    "last_name": "Smith"
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "id": 12,
    "email": "jane.doe@example.com",
    "first_name": "Janet",
    "last_name": "Smith",
    "full_name": "Janet Smith",
    "date_joined": "2026-05-18T02:00:00Z",
    "is_premium": false,
    "premium_expires_at": null,
    "free_minutes_used": 0,
    "purchased_credits": 0,
    "available_credits": 10,
    "free_minutes_remaining": 10
  }
  ```

---

## 📋 2. Clinical Intake Wizard

### 2.1 Submit Intake
* **Endpoint**: `POST /intake/create/`
* **Auth**: Protected (Bearer)
* **Description**: Submits the 9-step clinical intake wizard response. Automatically triggers NLP scanning using Claude AI to evaluate the details and populate the `problem_category` field before database insertion.
* **Request Body**:
  ```json
  {
    "main_issue": "I have been experiencing intense anxiety before work presentations and difficulty falling asleep.",
    "symptoms": ["insomnia", "racing thoughts", "heart palpitations"],
    "triggers": ["work meetings", "caffeine", "late night screens"],
    "session_duration_minutes": 10,
    "mood_before": 3,
    "has_inner_conflict": true,
    "repeating_thoughts": "I am going to fail and disappoint my team.",
    "negative_beliefs": "I am not competent enough to be in my role.",
    "ideal_outcome": "To feel calm, confident, and sleep restfully before important work days."
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "id": 1,
    "main_issue": "I have been experiencing intense anxiety before work presentations and difficulty falling asleep.",
    "problem_category": "insomnia_anxiety",
    "session_duration_minutes": 10,
    "mood_before": 3,
    "has_inner_conflict": true,
    "repeating_thoughts": "I am going to fail and disappoint my team.",
    "negative_beliefs": "I am not competent enough to be in my role.",
    "ideal_outcome": "To feel calm, confident, and sleep restfully before important work days.",
    "created_at": "2026-05-18T02:10:00Z",
    "updated_at": "2026-05-18T02:10:00Z",
    "user": 12
  }
  ```

### 2.2 List User Intakes
* **Endpoint**: `GET /intake/`
* **Auth**: Protected (Bearer)
* **Description**: Returns all historical clinical intake submissions created by the authenticated user in lightweight formats.
* **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "main_issue": "I have been experiencing intense anxiety before work presentations and difficulty falling asleep.",
      "problem_category": "insomnia_anxiety",
      "session_duration_minutes": 10,
      "created_at": "2026-05-18T02:10:00Z"
    }
  ]
  ```

### 2.3 Get Intake Details
* **Endpoint**: `GET /intake/<id>/`
* **Auth**: Protected (Bearer)
* **Description**: Retrieves complete clinical questions and NLP tags for a specific intake.
* **Response (200 OK)**: See 2.1 response payload.

---

## 🎧 3. Asynchronous Therapy Sessions

### 3.1 Initiate Session Generation
* **Endpoint**: `POST /sessions/create/`
* **Auth**: Protected (Bearer)
* **Description**: Triggers hypnotherapy session generation. Deducts credits from the user ledger atomically inside a transaction. Queues an asynchronous task to Celery to call Claude 3.5 Sonnet (for prompt generation) and ElevenLabs (for TTS compilation) in the background. Returns `202 Accepted` immediately.
* **Request Body**:
  ```json
  {
    "intake_id": 1,
    "duration_minutes": 10
  }
  ```
* **Response (202 Accepted)**:
  ```json
  {
    "id": 48,
    "status": "pending",
    "duration_minutes": 10,
    "credits_used": 10,
    "problem_category": "insomnia_anxiety",
    "audio_url": null,
    "error_message": null,
    "created_at": "2026-05-18T02:12:00Z",
    "user": 12,
    "intake": 1,
    "program_day_id": null
  }
  ```
* **Response (402 Payment Required — Insufficient Credits)**:
  ```json
  {
    "error": true,
    "detail": "Insufficient credits.",
    "required": 10,
    "available": 4
  }
  ```

### 3.2 List User Sessions
* **Endpoint**: `GET /sessions/`
* **Auth**: Protected (Bearer)
* **Description**: Returns all sessions created by the user. Supports status query filtering: `/sessions/?status=completed`.
* **Response (200 OK)**:
  ```json
  [
    {
      "id": 48,
      "status": "completed",
      "duration_minutes": 10,
      "problem_category": "insomnia_anxiety",
      "audio_url": "https://quantum-mind-audio-assets-production.s3.amazonaws.com/sessions/session_48.mp3",
      "created_at": "2026-05-18T02:12:00Z"
    }
  ]
  ```

### 3.3 Poll Session Status / Details
* **Endpoint**: `GET /sessions/<id>/`
* **Auth**: Protected (Bearer)
* **Description**: Retrieves full execution status, audio file endpoints, and background error details. Use this to poll generation completion.
* **Status Progression States**: `pending` ➔ `generating_script` ➔ `generating_audio` ➔ `completed` / `failed` (if failed, credits are automatically refunded to the user ledger).
* **Response (200 OK — Active Processing)**:
  ```json
  {
    "id": 48,
    "status": "generating_audio",
    "duration_minutes": 10,
    "credits_used": 10,
    "problem_category": "insomnia_anxiety",
    "audio_url": null,
    "error_message": null,
    "created_at": "2026-05-18T02:12:00Z",
    "user": 12,
    "intake": 1,
    "program_day_id": null
  }
  ```
* **Response (200 OK — Completed & Playable)**:
  ```json
  {
    "id": 48,
    "status": "completed",
    "duration_minutes": 10,
    "credits_used": 10,
    "problem_category": "insomnia_anxiety",
    "audio_url": "https://quantum-mind-audio-assets-production.s3.amazonaws.com/sessions/session_48.mp3",
    "error_message": null,
    "created_at": "2026-05-18T02:12:00Z",
    "user": 12,
    "intake": 1,
    "program_day_id": null
  }
  ```

---

## 💎 4. Credit Ledger System

### 4.1 Get Credit Balance
* **Endpoint**: `GET /credits/balance/`
* **Auth**: Protected (Bearer)
* **Description**: Returns detailed active, used, and total credit minute balances.
* **Response (200 OK)**:
  ```json
  {
    "free_minutes_total": 10,
    "free_minutes_used": 10,
    "free_minutes_remaining": 0,
    "purchased_credits": 25,
    "total_available": 25
  }
  ```

### 4.2 List Transactions (Immutable Audit Ledger)
* **Endpoint**: `GET /credits/transactions/`
* **Auth**: Protected (Bearer)
* **Description**: Returns chronological history logs of all credit balance changes (debits and refunds are recorded).
* **Response (200 OK)**:
  ```json
  [
    {
      "id": 5,
      "transaction_type": "session_use",
      "minutes_amount": -10,
      "description": "Used for generating session #48",
      "session_id": 48,
      "created_at": "2026-05-18T02:12:00Z"
    },
    {
      "id": 1,
      "transaction_type": "signup_bonus",
      "minutes_amount": 10,
      "description": "Free welcome tier minutes",
      "session_id": null,
      "created_at": "2026-05-18T02:00:00Z"
    }
  ]
  ```

### 4.3 List Credit Purchase Packages
* **Endpoint**: `GET /credits/packages/`
* **Auth**: Protected (Bearer)
* **Description**: Returns list of available merchant credit packages active on the platform.
* **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "name": "Standard Relaxation Pack",
      "minutes": 30,
      "price_cents": 1500,
      "price_dollars": 15.00,
      "sort_order": 1
    },
    {
      "id": 2,
      "name": "Premium Expansion Pack",
      "minutes": 100,
      "price_cents": 4000,
      "price_dollars": 40.00,
      "sort_order": 2
    }
  ]
  ```

---

## 📈 5. Mood & Adaptive AI Feedback

### 5.1 Log Mood Entry (Before Session)
* **Endpoint**: `POST /feedback/mood/create/`
* **Auth**: Protected (Bearer)
* **Description**: Creates a new mood entry record. Typically called right before playing a session.
* **Request Body**:
  ```json
  {
    "session_id": 48,
    "mood_before": 4,
    "notes": "Had a stressful call with client right now."
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "id": 3,
    "session_id": 48,
    "mood_before": 4,
    "mood_after": null,
    "improvement": null,
    "notes": "Had a stressful call with client right now.",
    "created_at": "2026-05-18T02:14:00Z"
  }
  ```

### 5.2 Log Mood Entry (After Session)
* **Endpoint**: `PATCH /feedback/mood/<id>/`
* **Auth**: Protected (Bearer)
* **Description**: Logs user mood score after a session is played. Automatically calculates `improvement`.
* **Request Body**:
  ```json
  {
    "mood_after": 8
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "id": 3,
    "session_id": 48,
    "mood_before": 4,
    "mood_after": 8,
    "improvement": 4,
    "notes": "Had a stressful call with client right now.",
    "created_at": "2026-05-18T02:14:00Z"
  }
  ```

### 5.3 Submit Post-Session Feedback
* **Endpoint**: `POST /feedback/session/`
* **Auth**: Protected (Bearer)
* **Description**: Submits details about therapeutic techniques that worked or failed. Triggers real-time rebuilding of the user's custom `TherapeuticProfile`.
* **Request Body**:
  ```json
  {
    "session_id": 48,
    "effectiveness_rating": 5,
    "techniques_resonated": ["Timeline Therapy", "Visual Anchoring"],
    "techniques_to_adjust": ["Pacing"],
    "general_notes": "The visual anchor of the calm beach helped me feel highly grounded."
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "id": 2,
    "session_id": 48,
    "effectiveness_rating": 5,
    "techniques_resonated": [
      "Timeline Therapy",
      "Visual Anchoring"
    ],
    "techniques_to_adjust": [
      "Pacing"
    ],
    "general_notes": "The visual anchor of the calm beach helped me feel highly grounded.",
    "created_at": "2026-05-18T02:30:00Z"
  }
  ```

### 5.4 Get Adaptive AI Profile
* **Endpoint**: `GET /feedback/profile/`
* **Auth**: Protected (Bearer)
* **Description**: Retrieves compiled AI therapeutic insights for the current user. This is injected as "Returning User Context" to customize all future AI script formulations.
* **Response (200 OK)**:
  ```json
  {
    "most_effective_techniques": [
      "Timeline Therapy",
      "Visual Anchoring"
    ],
    "least_effective_techniques": [
      "Pacing"
    ],
    "average_mood_improvement_by_category": {
      "insomnia_anxiety": 4.0
    },
    "session_count": 1,
    "key_themes": [
      "work deadline",
      "client call"
    ],
    "updated_at": "2026-05-18T02:30:05Z"
  }
  ```

### 5.5 List Mood History
* **Endpoint**: `GET /feedback/mood/`
* **Auth**: Protected (Bearer)
* **Description**: Returns all historical mood logs of the current user.
* **Response (200 OK)**:
  ```json
  [
    {
      "id": 3,
      "session_id": 48,
      "mood_before": 4,
      "mood_after": 8,
      "improvement": 4,
      "notes": "Had a stressful call with client right now.",
      "created_at": "2026-05-18T02:14:00Z"
    }
  ]
  ```

---

## 🗺️ 6. Multi-Day Therapeutic Programs

### 6.1 List Programs
* **Endpoint**: `GET /programs/`
* **Auth**: Protected (Bearer)
* **Description**: Returns all active multi-day programs. Non-premium users only see standard programs; premium-only programs are filtered out unless they are subscribed.
* **Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "name": "7-Day Performance Confidence Program",
      "description": "Unlock confidence and melt presentation anxiety in one week.",
      "total_days": 7,
      "category": "confidence",
      "is_premium_only": false,
      "thumbnail_url": "https://quantum-mind-cdn.com/thumbs/confidence_7.jpg",
      "enrolled": false
    }
  ]
  ```

### 6.2 Get Program Details (With Days)
* **Endpoint**: `GET /programs/<id>/`
* **Auth**: Protected (Bearer)
* **Description**: Retrieves full program instructions along with each individual program day focus.
* **Response (200 OK)**:
  ```json
  {
    "id": 1,
    "name": "7-Day Performance Confidence Program",
    "description": "Unlock confidence and melt presentation anxiety in one week.",
    "total_days": 7,
    "category": "confidence",
    "is_premium_only": false,
    "thumbnail_url": "https://quantum-mind-cdn.com/thumbs/confidence_7.jpg",
    "sort_order": 1,
    "enrolled": false,
    "days": [
      {
        "id": 1,
        "day_number": 1,
        "title": "Mapping the Presentation Stress",
        "description": "Examine physical triggers and somatic response details.",
        "focus_technique": "Somatic Scan & Release"
      },
      {
        "id": 2,
        "day_number": 2,
        "title": "Establishing somatic calm anchors",
        "description": "Associate safety triggers with deep breathing triggers.",
        "focus_technique": "Calm Anchoring Integration"
      }
    ]
  }
  ```

### 6.3 Enroll in Program
* **Endpoint**: `POST /programs/enroll/`
* **Auth**: Protected (Bearer)
* **Description**: Enrolls the user into a multi-day journey.
* **Request Body**:
  ```json
  {
    "program_id": 1
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "id": 4,
    "program": {
      "id": 1,
      "name": "7-Day Performance Confidence Program",
      "description": "Unlock confidence and melt presentation anxiety in one week.",
      "total_days": 7,
      "category": "confidence",
      "is_premium_only": false,
      "thumbnail_url": "https://quantum-mind-cdn.com/thumbs/confidence_7.jpg",
      "enrolled": true
    },
    "current_day": 1,
    "status": "active",
    "progress_percentage": 14,
    "current_program_day": {
      "id": 1,
      "day_number": 1,
      "title": "Mapping the Presentation Stress",
      "description": "Examine physical triggers and somatic response details.",
      "focus_technique": "Somatic Scan & Release"
    },
    "started_at": "2026-05-18T02:40:00Z",
    "completed_at": null
  }
  ```

### 6.4 Get Active Enrollments
* **Endpoint**: `GET /programs/my-enrollments/`
* **Auth**: Protected (Bearer)
* **Description**: Returns all active and finished program enrollments of the user.
* **Response (200 OK)**:
  ```json
  [
    {
      "id": 4,
      "program": {
        "id": 1,
        "name": "7-Day Performance Confidence Program",
        "description": "Unlock confidence and melt presentation anxiety in one week.",
        "total_days": 7,
        "category": "confidence",
        "is_premium_only": false,
        "thumbnail_url": "https://quantum-mind-cdn.com/thumbs/confidence_7.jpg",
        "enrolled": true
      },
      "current_day": 1,
      "status": "active",
      "progress_percentage": 14,
      "current_program_day": {
        "id": 1,
        "day_number": 1,
        "title": "Mapping the Presentation Stress",
        "description": "Examine physical triggers and somatic response details.",
        "focus_technique": "Somatic Scan & Release"
      },
      "started_at": "2026-05-18T02:40:00Z",
      "completed_at": null
    }
  ]
  ```

### 6.5 Advance Program Day / Mark Day Completed
* **Endpoint**: `POST /programs/enrollments/<id>/advance/`
* **Auth**: Protected (Bearer)
* **Description**: Marks the current day as completed and advances progress to the next day. If the current day equals total program days, the program is marked `completed`.
* **Request Body**: `None` (triggers progression based on the URL path ID parameter)
* **Response (200 OK — Active Progress)**:
  ```json
  {
    "id": 4,
    "program": {
      "id": 1,
      "name": "7-Day Performance Confidence Program",
      "description": "Unlock confidence and melt presentation anxiety in one week.",
      "total_days": 7,
      "category": "confidence",
      "is_premium_only": false,
      "thumbnail_url": "https://quantum-mind-cdn.com/thumbs/confidence_7.jpg",
      "enrolled": true
    },
    "current_day": 2,
    "status": "active",
    "progress_percentage": 28,
    "current_program_day": {
      "id": 2,
      "day_number": 2,
      "title": "Establishing somatic calm anchors",
      "description": "Associate safety triggers with deep breathing triggers.",
      "focus_technique": "Calm Anchoring Integration"
    },
    "started_at": "2026-05-18T02:40:00Z",
    "completed_at": null
  }
  ```
* **Response (200 OK — Journey Fully Completed)**:
  ```json
  {
    "detail": "Program completed!",
    "id": 4,
    "program": {
      "id": 1,
      "name": "7-Day Performance Confidence Program",
      "description": "Unlock confidence and melt presentation anxiety in one week.",
      "total_days": 7,
      "category": "confidence",
      "is_premium_only": false,
      "thumbnail_url": "https://quantum-mind-cdn.com/thumbs/confidence_7.jpg",
      "enrolled": true
    },
    "current_day": 7,
    "status": "completed",
    "progress_percentage": 100,
    "current_program_day": null,
    "started_at": "2026-05-18T02:40:00Z",
    "completed_at": "2026-05-18T03:00:00Z"
  }
  ```
