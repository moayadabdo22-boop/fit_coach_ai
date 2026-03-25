**Backend Templates (FastAPI)**

Router layout
- `routers/users.py`
- `routers/plans.py`
- `routers/analytics.py`
- `routers/ai.py`
- `routers/admin.py`

Pydantic models (sample)
```python
from pydantic import BaseModel, Field
from typing import List, Optional

class GoalRef(BaseModel):
    goal_code: str
    priority: int = 1

class ProfileUpdate(BaseModel):
    full_name: Optional[str]
    gender: Optional[str]
    birth_date: Optional[str]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    body_fat_pct: Optional[float]
    fitness_level: Optional[str]
    goal_primary: Optional[str]

class WorkoutPlanRequest(BaseModel):
    goal_code: str
    fitness_level: str
    equipment_available: List[str] = []
    days_per_week: int = 3
    injuries: List[str] = []
```

Service skeleton
```python
class WorkoutPlanService:
    def generate(self, user_snapshot, constraints):
        # 1) retrieval
        # 2) rules
        # 3) assemble plan
        return plan_json
```

Background tasks
- Use Celery or RQ for ETL and model training.
- Store ETL jobs and statuses in DB.

Caching
- Redis for frequent reads (foods, exercises, last plan).

