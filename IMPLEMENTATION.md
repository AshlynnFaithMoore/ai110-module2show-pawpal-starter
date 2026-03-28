# PawPal+ System Implementation Summary

## Architecture Overview

The implementation follows the **Aggregation via Owner (Pattern 1)** design for clean separation of concerns:

- **Owner** is the facade that aggregates pet data and validates time constraints
- **Scheduler** pulls from Owner (not the reverse), keeping concerns isolated
- **Pet** remains passive, storing pet profile and task list
- **Task** is a data-heavy class with validation and utility methods

## Key Design Decisions

### 1. Single vs. Multi-Pet Support
- The system supports **multiple pets per Owner** but initializes with a single pet for the MVP
- Future: scale to multi-pet scheduling without API changes by extending `generate_daily_plan()` to iterate over pets

### 2. Validation Early
- **Task** validates: duration > 0, priority ∈ {low, medium, high}, due_by time format
- **Owner** validates: budget > 0, time format (HH:MM), end_time > start_time
- Errors raised in `__post_init__()` catch bugs at object creation time

### 3. Ranking Strategy: Deterministic Multi-Criterion Sort
Scheduler ranks tasks in this priority order:
1. Required (required=True) before optional
2. Higher priority (high > medium > low) first
3. Earlier due_by times first
4. Shorter durations first (maximize flexibility)
5. Alphabetical title for deterministic tie-breaking

### 4. Plan Caching & Explainability
- `Scheduler.generate_daily_plan()` caches the plan in `self.plan`
- `Scheduler.explain_plan()` can reference `self.plan` by default or accept external plan for flexibility
- Each `ScheduleItem` includes a `reason` field for user-facing justification

### 5. Time Window Constraints
- Tasks with `due_by` must fall within Owner's `preferred_start_time` and `preferred_end_time`
- Schedule can never exceed `preferred_end_time`
- Buffer (`buffer_minutes`) reserves time for flexibility or padding

## Class API Summary

### Owner
- `add_pet(pet)` — register a pet with this owner
- `get_pets()` — retrieve all pets
- `get_all_tasks()` — aggregate all active tasks from all pets
- `set_time_budget(minutes)` — update daily budget
- `set_preferred_window(start, end)` — update HH:MM window
- `can_fit(total_minutes)` — check if duration fits budget

### Pet
- `add_task(task)` — add task to pet's list
- `remove_task(task_id)` — remove by ID (return bool)
- `get_active_tasks()` — filter to active=True tasks

### Task
- `priority_weight()` — numeric weight for sorting
- `is_due_window_valid(owner)` — check if task's due_by fits owner's window
- `summary()` — human-readable string

### Scheduler
- `rank_tasks(tasks)` — sort by criteria
- `generate_daily_plan(owner, pet)` → ScheduleItem[] — build and cache plan
- `explain_plan(owner, plan)` → str[] — human-readable reasons

## Testing Coverage

Tests in `tests/test_pawpal.py` cover:
- Task validation (duration, priority, time format)
- Owner constraints (budget, time window, pet management)
- Pet task management (add, remove, active filtering)
- Scheduler ranking (priority, required flag, due time, determinism)
- Plan generation (budget respect, buffer behavior, window constraints)
- Plan explanations (reason generation)

## Future Extensions

1. **Multi-pet scheduling**: Extend `generate_daily_plan()` to return `dict[pet_id, ScheduleItem[]]`
2. **Recurring tasks**: Add frequency field to Task (daily, weekly, etc.)
3. **Advanced strategies**: Add new `Scheduler.strategy` options (e.g., "time_slots", "energy_based")
4. **Conflict detection**: Check for overlapping due times across tasks
5. **Notification system**: Emit alerts if plan can't fit all required tasks
