**AI Fitness Platform API Spec (FastAPI)**

Base URL: `/api/v1`

Auth
1. `POST /auth/signup`
  Request: `{ email, password, full_name }`
  Response: `{ user_id, email, requires_email_confirm }`
1. `POST /auth/login`
  Request: `{ email, password }`
  Response: `{ access_token, refresh_token, user_id }`
1. `POST /auth/refresh`
  Request: `{ refresh_token }`
  Response: `{ access_token, refresh_token }`

Users & Profile
1. `GET /users/me`
  Response: `{ profile, goals, conditions, allergies, preferences }`
1. `PUT /users/me/profile`
  Request: `{ full_name, gender, birth_date, height_cm, weight_kg, body_fat_pct, fitness_level, goal_primary }`
  Response: `{ profile }`
1. `PUT /users/me/preferences`
  Request: `{ diet_style, favorite_foods, disliked_foods, workout_time, equipment_available, avoid_equipment }`
  Response: `{ preferences }`
1. `PUT /users/me/goals`
  Request: `{ goals: [{ goal_code, priority }] }`
  Response: `{ goals }`
1. `PUT /users/me/conditions`
  Request: `{ conditions: [{ condition_code, severity, notes }] }`
  Response: `{ conditions }`
1. `PUT /users/me/allergies`
  Request: `{ allergies: [{ allergen_code, severity }] }`
  Response: `{ allergies }`

Foods & Nutrition
1. `GET /foods/search?q=chicken`
  Response: `{ items: [{ id, name, calories, macros, allergens }] }`
1. `GET /foods/{id}`
  Response: `{ food, nutrients, allergens }`

Meal Plans
1. `POST /meal-plans/generate`
  Request: `{ goal_code, calories_target, diet_style, allergies, conditions }`
  Response: `{ plan_id, plan_json }`
1. `POST /meal-plans/{id}/approve`
  Response: `{ saved: true }`
1. `GET /meal-plans`
  Response: `{ items: [plan] }`
1. `PUT /meal-plans/{id}/activate`
  Response: `{ active: true }`

Exercises & Workouts
1. `GET /exercises/search?q=squat&muscle=legs&equipment=barbell`
  Response: `{ items: [{ id, name, muscle_groups, difficulty, met }] }`
1. `POST /workout-plans/generate`
  Request: `{ goal_code, fitness_level, equipment_available, days_per_week, injuries }`
  Response: `{ plan_id, plan_json }`
1. `POST /workout-plans/{id}/approve`
  Response: `{ saved: true }`
1. `GET /workout-plans`
  Response: `{ items: [plan] }`
1. `PUT /workout-plans/{id}/activate`
  Response: `{ active: true }`

Progress & Analytics
1. `POST /progress/logs`
  Request: `{ log_date, weight_kg, body_fat_pct, sleep_hours, calories_in, calories_out, notes }`
  Response: `{ log }`
1. `GET /progress/logs?from=2026-01-01&to=2026-01-31`
  Response: `{ items: [log] }`
1. `GET /analytics/summary?range=weekly`
  Response: `{ adherence_score, trends, plateaus }`
1. `GET /analytics/reports?range=monthly`
  Response: `{ report_url }`

AI Coach (RAG)
1. `POST /coach/chat`
  Request: `{ message, user_id, conversation_id, language }`
  Response: `{ reply, action, data }`
1. `GET /coach/memory/{conversation_id}`
  Response: `{ messages }`
1. `POST /coach/feedback`
  Request: `{ recommendation_id, rating, comment }`
  Response: `{ saved: true }`

Gamification & Notifications
1. `GET /gamification/summary`
  Response: `{ points, level, badges, streaks }`
1. `POST /notifications`
  Request: `{ title, body, scheduled_at }`
  Response: `{ id }`
1. `GET /notifications`
  Response: `{ items: [notification] }`

Admin
1. `POST /admin/etl/foods`
  Response: `{ started: true, job_id }`
1. `POST /admin/etl/exercises`
  Response: `{ started: true, job_id }`

