# AI-Powered Personalized Fitness Coaching Platform
## Graduation Project Proposal (Final Draft)

**Student:** Moayad Abdo  \
**Program:** Artificial Intelligence  \
**Project Type:** Applied AI System (ML + RAG + LLM + Validation + Deployment)  \
**Workflow Backbone:** Profile data ? Feature engineering ? ML goal classifier ? RAG retrieval ? LLM plan generation ? Validation ? Plan selection ? Schedule storage

---

## Abstract
This proposal presents an AI-powered fitness coaching platform that generates safe, personalized workout and nutrition plans using a strict end-to-end workflow. The system starts from user profile and behavior data, engineers medically and training-relevant features, predicts the most suitable goal using supervised machine learning, retrieves trusted domain knowledge through Retrieval-Augmented Generation (RAG), and generates candidate plans with a Large Language Model (LLM). Every generated plan then passes a deterministic validation layer (medical constraints, training load bounds, and nutrition sanity checks) before the user selects a plan and stores it in a persistent schedule. The project is designed as a real AI system, not a static chatbot, and will be evaluated with measurable metrics on classification quality, retrieval quality, generation quality, safety compliance, and user progress outcomes.

## 1. Introduction
Most fitness applications provide generic programs that are not adapted to user physiology, progress trend, or adherence behavior. This project addresses that limitation by combining machine learning, retrieval, and controlled LLM generation into one production-style architecture. The target is to deliver a measurable intelligent coach that can explain recommendations, estimate progress timelines, and remain safe under practical constraints.

## 2. Problem Statement
Current market solutions often fail in one or more of the following:
- static plans not tied to user-specific trends;
- weak adaptation to changing adherence and recovery;
- no reliable safety validation before recommendation;
- chatbot responses that appear intelligent but are mainly template-based;
- limited academic evaluation of AI quality.

This project solves these gaps by implementing a strict AI workflow with measurable gates and persistence.

## 3. Project Objectives
### 3.1 Primary Objective
Design and implement a full AI planning pipeline that transforms user data into validated, personalized workout/nutrition schedules with measurable performance impact.

### 3.2 Technical Objectives
- Build a robust feature engineering layer (BMI, BMR, TDEE, adherence, trend, and load features).
- Train and evaluate a supervised goal classifier (fat-loss, muscle-gain, general-fitness).
- Implement RAG over trusted local datasets and knowledge files for evidence-grounded suggestions.
- Generate plans using LLM with structured JSON output constraints.
- Validate plan safety and feasibility before user approval.
- Persist approved plans and completion logs in schedule storage for progress analytics.

## 4. Scope
### In Scope
- Fitness-domain conversations only (workouts, nutrition, progress, schedule).
- Personalized workout and nutrition planning.
- Weekly/monthly progress analysis and ETA estimation to goal.
- Multilingual interaction (English and Arabic) at interface level.

### Out of Scope
- Clinical diagnosis and emergency medical advice.
- Non-fitness general knowledge assistant behavior.
- Fully autonomous coaching without user approval.

## 5. Proposed End-to-End AI Workflow (Core Requirement)

### Step 1: Profile Data
Input sources include demographics (age, sex), anthropometrics (height, weight), goal preference, health constraints, activity level, workout logs, and adherence history from schedule completion records.

### Step 2: Feature Engineering
The system computes derived features such as BMI, estimated BMR, estimated TDEE, weight trend (last 4 weeks), workout adherence %, sleep/protein consistency, and volume/fatigue indicators. These features become the canonical representation for ML and plan conditioning.

### Step 3: ML Goal Classifier
A supervised classifier predicts the most probable goal class from engineered features and behavior signals. Output includes class probabilities and confidence, enabling uncertainty-aware fallback policy.

### Step 4: RAG Retrieval
The retriever queries curated fitness/nutrition datasets and knowledge chunks, returning top-k evidence snippets with scores. Retrieved evidence is attached to generation context to reduce hallucination and improve domain grounding.

### Step 5: LLM Plan Generation
The LLM receives structured context: profile summary, engineered features, predicted goal, and retrieved evidence. It generates multiple candidate plans in strict JSON schema (workout days, sets, reps, rest, calories/macros where relevant).

### Step 6: Validation
A deterministic validator checks safety and feasibility rules (contraindication rules, volume limits, progression bounds, macro/calorie plausibility, required fields completeness). Invalid plans are rejected and regenerated.

### Step 7: Plan Selection
Validated candidate plans are presented to the user with concise comparison metadata (difficulty, expected adherence, target fit). The user explicitly approves one plan.

### Step 8: Schedule Storage
Approved plans are saved into persistent storage, activated in the schedule module, and linked to completion tracking. This closes the loop for future feature updates and progress analysis.

## 6. System Architecture
### 6.1 Frontend
- React-based UI for chat, workouts, schedule, and profile forms.
- Sends structured payloads (profile, tracking summary, plan snapshot, recent messages).
- Displays candidate plans, approval actions, and progress outputs.

### 6.2 Backend API
- FastAPI service as orchestration layer.
- Dedicated modules: `feature_service`, `ml_service`, `rag_service`, `llm_service`, `validation_service`, `plan_service`.
- Clear stage-wise tracing and error handling per workflow step.

### 6.3 Data and Storage
- Supabase/PostgreSQL for profiles, plans, completions, and chat history.
- Dataset files for workout/nutrition/conversation intents as local knowledge assets.
- Model artifacts (`.pkl`) with metadata and versioning.

### 6.4 LLM and Runtime
- Local-first inference via Ollama (free deployment path).
- Optional cloud fallback provider for reliability tests.
- Strict prompt + structured output policy (JSON schema).

## 7. Datasets and Data Strategy
- Use existing project datasets for workout, nutrition, and domain conversation intents.
- Apply cleaning, schema alignment, deduplication, and label audit.
- Split data by reproducible strategy (train/validation/test).
- Track source provenance to support academic transparency.

## 8. Modeling and AI Methods
### 8.1 Goal Classification
- Baseline: logistic regression / random forest over engineered features.
- Output: class + probability distribution + confidence thresholding.

### 8.2 Retrieval Layer (RAG)
- Chunking policy for textual knowledge.
- Embedding + top-k retrieval with fallback lexical search.
- Retrieval quality measured with precision@k and relevance scoring.

### 8.3 LLM Generation
- Prompted with grounded evidence and strict schema instructions.
- Generates multiple candidates for selection and safety filtering.
- Hallucination control via evidence-only domain constraints.

## 9. Validation and Safety Framework
Validation rules include:
- hard constraints on missing required fields;
- intensity/volume boundaries by user level;
- contraindication checks from chronic conditions and injuries;
- nutrition plausibility checks (calories/macros consistency);
- scope checks for out-of-domain requests with safe refusal.

Only validated plans move to user selection.

## 10. Evaluation Plan (Academic Quality)
### 10.1 ML Metrics
- Accuracy, Precision, Recall, F1 (macro + weighted).
- Calibration and confusion matrix by class.

### 10.2 RAG Metrics
- Precision@k, Recall@k (if labeled), and human relevance scoring.
- Evidence coverage and citation consistency.

### 10.3 Generation/Validation Metrics
- Plan validity rate (% passing validator on first attempt).
- Regeneration rate and failure categories.
- Safety violation rate (must approach zero).

### 10.4 Product Metrics
- Response latency by stage.
- User adherence trend after plan adoption.
- Estimated time-to-goal stability over 4-week windows.

## 11. Implementation Roadmap
1. Freeze final schema for profile/tracking/plan objects.
2. Build standalone feature engineering service + tests.
3. Retrain and benchmark goal classifier with reproducible splits.
4. Deploy robust RAG index and relevance evaluation.
5. Add structured LLM generation with JSON schema enforcement.
6. Implement deterministic validation gate and error taxonomy.
7. Implement backend-owned approval and schedule persistence transaction flow.
8. Add monitoring dashboards and experiment logging.
9. Run ablation study: rule-based vs full pipeline.
10. Final integration test and report packaging.

## 12. Timeline (12 Weeks)
- **Weeks 1?2:** Data schema finalization, feature definitions, baseline preprocessing.
- **Weeks 3?4:** Goal classifier training, evaluation, and calibration.
- **Weeks 5?6:** RAG indexing, retrieval tuning, relevance benchmark.
- **Weeks 7?8:** LLM structured generation + validation engine.
- **Weeks 9?10:** End-to-end orchestration, backend persistence, frontend integration.
- **Week 11:** Full evaluation, ablation, stress testing.
- **Week 12:** Documentation, final demo, thesis/presentation packaging.

## 13. Deliverables
- Final architecture document with stage-by-stage data flow.
- Trained ML models with evaluation report and reproducibility details.
- RAG index build scripts and retrieval evaluation report.
- Validated plan-generation engine with safety rules.
- Integrated web platform with chat, plan selection, and schedule storage.
- Final technical report and demonstration video.

## 14. Expected Contribution
This project contributes an academically defensible blueprint for practical AI coaching systems by combining supervised prediction, retrieval grounding, controlled LLM generation, and deterministic safety validation in one measurable loop.

## 15. Risks and Mitigation
- **Risk:** Weak retrieval quality. **Mitigation:** curated corpus + retrieval evaluation + fallback strategy.
- **Risk:** LLM invalid JSON outputs. **Mitigation:** strict schema parser + automatic regeneration.
- **Risk:** Unsafe recommendations. **Mitigation:** hard validator rules + out-of-scope refusal layer.
- **Risk:** Data drift. **Mitigation:** periodic retraining and confidence monitoring.

## 16. Conclusion
The proposed system is designed to satisfy graduation-level AI expectations through a complete, measurable, and safety-aware workflow. It goes beyond template chatbot behavior by enforcing data-driven prediction, retrieval grounding, structured generation, and validated scheduling. This proposal is ready for academic submission and implementation as a strong AI capstone project.

## Appendix A: Workflow Compliance Checklist
- [ ] Profile data ingestion is mandatory before planning.
- [ ] Feature engineering is explicit and test-covered.
- [ ] Goal classifier inference includes confidence.
- [ ] RAG retrieval returns top-k evidence snippets with scores.
- [ ] LLM output must match strict JSON schema.
- [ ] Validation gate blocks unsafe/invalid plans.
- [ ] User must select from validated options.
- [ ] Approved plan is stored persistently in schedule storage.
- [ ] Completion logs feed next feature update cycle.
- [ ] All stages are observable via logs/metrics for auditing.