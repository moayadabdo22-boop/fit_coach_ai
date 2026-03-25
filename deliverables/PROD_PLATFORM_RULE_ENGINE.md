**Medical & Safety Rule Engine**

Rule Types
1. Disease-based dietary restrictions
2. Injury-based exercise exclusions
3. Intensity limits by age and recovery score
4. Medication-nutrition flags (optional if medication data exists)

Rule Evaluation Order
1. Hard Exclusions (must remove)
2. Risk Mitigations (limit intensity/volume)
3. Suggestions (swap alternatives)

Example Rules (pseudo-code)
1. Diabetes (diet)
  - If user has condition "diabetes"
  - Filter foods with high glycemic index (GI > 70)
  - Prefer high fiber and low sugar foods

2. Hypertension (diet)
  - If condition "hypertension"
  - Limit sodium_mg > 500 per serving
  - Avoid processed foods

3. Knee Injury (workout)
  - Exclude deep squats, jumps, high-impact running
  - Substitute low-impact exercises (bike, swimming)

4. Shoulder Injury (workout)
  - Exclude overhead press, snatch, heavy bench
  - Substitute landmine press or rows

5. Age > 55
  - Cap intensity at RPE 7
  - Increase rest interval by 25%
  - Reduce weekly volume by 15%

6. Recovery score < 60
  - Reduce intensity by 20%
  - Add mobility/rest day

Override Behavior
- Any rule conflict overrides AI plan output.
- Final plan must include `rules_applied` list.

Validation Checklist
- No excluded exercise present
- All meals respect allergy list
- Macro distribution within target range

