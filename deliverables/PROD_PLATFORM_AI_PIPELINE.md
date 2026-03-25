**AI Pipeline Architecture (RAG + Rules + Personalization)**

Overview
- Input: user message, profile, goals, conditions, preferences, recent progress.
- Output: structured JSON plans + friendly explanation.

Pipeline Steps
1. Input Guardrails
  - Domain routing (fitness/nutrition only)
  - Content moderation
  - Safety checks (age, injuries)

2. Snapshot Builder
  - Fetch structured user context from DB
  - Build `user_snapshot` (profile, goals, conditions, allergies, preferences)
  - Pull latest progress metrics and adherence

3. Retrieval (RAG)
  - Query exercise DB by goals, equipment, muscle focus
  - Query foods DB by calories, macros, allergies, conditions
  - Include recent user plan context and progress

4. Deterministic Rule Engine
  - Apply hard constraints (medical restrictions, injury exclusions)
  - Filter incompatible foods/exercises
  - Set intensity caps based on recovery score

5. Generator
  - Workout Plan Generator (periodization + progressive overload)
  - Nutrition Plan Generator (BMR/TDEE + macro targets)
  - Output JSON plan template

6. Personalization Adjuster
  - Modify plan using adherence and plateau signals
  - Adjust volume or calories weekly

7. Validation
  - Schema validation on JSON output
  - Conflicts resolved by rules (rules override)

8. Response Composer
  - Human readable summary referencing real data
  - Ask for missing data if required

Artifacts
- `user_snapshot.json`
- `retrieved_exercises.json`
- `retrieved_foods.json`
- `plan_output.json`
- `audit_log.json`

Plan JSON Contract (example)
```json
{
  "type": "workout",
  "title": "Strength Focus Plan",
  "duration_days": 7,
  "days": [
    {
      "day": "Monday",
      "exercises": [
        { "name": "Barbell Squat", "sets": 4, "reps": 6, "rest_sec": 120 }
      ]
    }
  ],
  "rules_applied": ["knee_injury_exclusion", "beginner_volume_cap"]
}
```

