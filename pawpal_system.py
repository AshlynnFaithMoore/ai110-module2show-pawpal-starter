from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, TypedDict

# Priority mapping for sorting and weighting
PRIORITY_WEIGHTS = {"low": 1, "medium": 2, "high": 3}


class ScheduleItem(TypedDict):
    """Represents one task in the daily schedule."""
    task_id: str
    task_title: str
    duration_minutes: int
    priority: str
    start_time: str
    end_time: str
    reason: str


def _parse_hhmm(value: str) -> datetime:
    """Parse HH:MM time string into a datetime object (today's date)."""
    return datetime.strptime(value, "%H:%M")


@dataclass
class Owner:
    """Represents the pet owner and their planning constraints."""
    owner_id: str
    name: str
    daily_time_budget_minutes: int = 60
    preferred_start_time: str = "08:00"
    preferred_end_time: str = "20:00"
    pets: list[Pet] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate owner attributes on creation."""
        if self.daily_time_budget_minutes <= 0:
            raise ValueError("Daily time budget must be greater than 0")
        try:
            _parse_hhmm(self.preferred_start_time)
            _parse_hhmm(self.preferred_end_time)
        except ValueError as e:
            raise ValueError(f"Invalid time format (use HH:MM): {e}")
        start = _parse_hhmm(self.preferred_start_time)
        end = _parse_hhmm(self.preferred_end_time)
        if end <= start:
            raise ValueError("Preferred end time must be after start time")

    def set_time_budget(self, minutes: int) -> None:
        """Update the daily time budget for pet care tasks."""
        if minutes <= 0:
            raise ValueError("Time budget must be greater than 0")
        self.daily_time_budget_minutes = minutes

    def set_preferred_window(self, start: str, end: str) -> None:
        """Update the preferred planning window (HH:MM format)."""
        try:
            start_dt = _parse_hhmm(start)
            end_dt = _parse_hhmm(end)
        except ValueError as e:
            raise ValueError(f"Invalid time format (use HH:MM): {e}")
        if end_dt <= start_dt:
            raise ValueError("Preferred end time must be after start time")
        self.preferred_start_time = start
        self.preferred_end_time = end

    def can_fit(self, total_minutes: int) -> bool:
        """Check if total_minutes fits within the daily budget."""
        return total_minutes <= self.daily_time_budget_minutes

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)
        pet.owner = self

    def get_pets(self) -> list[Pet]:
        """Retrieve all pets owned by this owner."""
        return self.pets

    def get_all_tasks(self) -> list[Task]:
        """Aggregate and return all tasks from all pets."""
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_active_tasks())
        return all_tasks


@dataclass
class Task:
    """Represents a single pet care task."""
    task_id: str
    title: str
    category: str
    duration_minutes: int
    priority: str
    frequency: str = "once"
    due_date: Optional[str] = None
    required: bool = False
    due_by: Optional[str] = None
    active: bool = True
    completed: bool = False

    def __post_init__(self) -> None:
        """Validate task attributes on creation."""
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be greater than 0")
        if self.priority not in PRIORITY_WEIGHTS:
            raise ValueError(f"Task priority must be one of {list(PRIORITY_WEIGHTS.keys())}")
        if self.frequency not in {"once", "daily", "weekly"}:
            raise ValueError("Task frequency must be one of: once, daily, weekly")
        if self.due_date is not None:
            try:
                datetime.strptime(self.due_date, "%Y-%m-%d")
            except ValueError as e:
                raise ValueError(f"Invalid due_date format (use YYYY-MM-DD): {e}")
        if self.due_by is not None:
            try:
                _parse_hhmm(self.due_by)
            except ValueError as e:
                raise ValueError(f"Invalid due_by time format (use HH:MM): {e}")

    def priority_weight(self) -> int:
        """Return numeric weight for this task's priority (for sorting)."""
        return PRIORITY_WEIGHTS.get(self.priority, 0)

    def is_due_window_valid(self, owner: Owner) -> bool:
        """Check if task's due_by time (if set) falls within owner's preferred window."""
        if self.due_by is None:
            return True
        due_time = _parse_hhmm(self.due_by)
        start_time = _parse_hhmm(owner.preferred_start_time)
        end_time = _parse_hhmm(owner.preferred_end_time)
        return start_time <= due_time <= end_time

    def summary(self) -> str:
        """Return a human-readable summary of the task."""
        required_text = "required" if self.required else "optional"
        return f"{self.title} ({self.duration_minutes} min, {self.priority}, {required_text})"

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def mark_incomplete(self) -> None:
        """Mark this task as not completed."""
        self.completed = False

    def create_next_occurrence(self) -> Optional[Task]:
        """Return a new task for the next daily/weekly occurrence, or None for one-time tasks."""
        if self.frequency not in {"daily", "weekly"}:
            return None

        base_date = datetime.today().date()
        if self.due_date is not None:
            base_date = datetime.strptime(self.due_date, "%Y-%m-%d").date()

        delta = timedelta(days=1 if self.frequency == "daily" else 7)
        next_date = (base_date + delta).strftime("%Y-%m-%d")

        return Task(
            task_id=f"{self.task_id}-next-{next_date}",
            title=self.title,
            category=self.category,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            frequency=self.frequency,
            due_date=next_date,
            required=self.required,
            due_by=self.due_by,
            active=True,
            completed=False,
        )


@dataclass
class Pet:
    """Represents a pet and manages its care tasks."""
    pet_id: str
    name: str
    species: str
    age: Optional[int] = None
    care_notes: str = ""
    owner: Optional[Owner] = None
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a new task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID; return True if removed, False if not found."""
        for i, task in enumerate(self.tasks):
            if task.task_id == task_id:
                self.tasks.pop(i)
                return True
        return False

    def get_active_tasks(self) -> list[Task]:
        """Return only active tasks (active=True)."""
        return [task for task in self.tasks if task.active]


class Scheduler:
    """Orchestrates task ranking and daily schedule generation."""

    def __init__(self, strategy: str = "priority_first", buffer_minutes: int = 0) -> None:
        """Initialize scheduler with a ranking strategy and optional time buffer.

        Args:
            strategy: Ranking algorithm name (e.g., 'priority_first').
            buffer_minutes: Minutes to reserve as a safety margin in the daily plan.
        """
        self.strategy = strategy
        self.buffer_minutes = buffer_minutes
        self.plan: list[ScheduleItem] = []

    def _due_sort_value(self, task: Task) -> int:
        """Return sort key for task's due_by time (early times first)."""
        if task.due_by is None:
            return 24 * 60 + 1  # No due time sorts last
        due_time = _parse_hhmm(task.due_by)
        return due_time.hour * 60 + due_time.minute

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by HH:MM `due_by` time, placing tasks with no time at the end."""
        return sorted(tasks, key=lambda task: task.due_by if task.due_by is not None else "99:99")

    def filter_tasks(
        self,
        owner: Owner,
        completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> list[Task]:
        """Return tasks filtered by optional completion status and/or pet name."""
        tasks: list[Task] = []
        for pet in owner.get_pets():
            if pet_name is not None and pet.name.lower() != pet_name.lower():
                continue
            tasks.extend(pet.tasks)

        if completed is not None:
            tasks = [task for task in tasks if task.completed == completed]

        return tasks

    def mark_task_complete(self, pet: Pet, task_id: str) -> Optional[Task]:
        """Complete an active task and auto-create its next instance for recurring frequencies."""
        for task in pet.tasks:
            if task.task_id == task_id and task.active:
                task.mark_complete()
                task.active = False
                next_task = task.create_next_occurrence()
                if next_task is not None:
                    pet.add_task(next_task)
                return next_task
        return None

    def rank_tasks(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by ranking criteria (required, priority, due time, duration, title)."""
        return sorted(
            tasks,
            key=lambda task: (
                0 if task.required else 1,  # Required tasks first
                -task.priority_weight(),  # Higher priority first (negative for reverse sort)
                self._due_sort_value(task),  # Earlier due times first
                task.duration_minutes,  # Shorter tasks first (for flexibility)
                task.title.lower(),  # Alphabetical for determinism
            ),
        )

    def generate_daily_plan(self, owner: Owner, pet: Pet) -> list[ScheduleItem]:
        """Build and cache a daily schedule for the pet within owner's constraints.

        Returns:
            List of ScheduleItem dicts with task, timing, and reasoning.
        """
        # Get ranked tasks for this pet
        active_tasks = pet.get_active_tasks()
        ranked_tasks = self.rank_tasks(active_tasks)

        # Calculate available time
        remaining_minutes = max(
            0, owner.daily_time_budget_minutes - self.buffer_minutes
        )

        # Parse owner's preferred window
        current_time = _parse_hhmm(owner.preferred_start_time)
        end_window = _parse_hhmm(owner.preferred_end_time)

        self.plan = []

        for task in ranked_tasks:
            # Skip tasks with invalid due windows
            if not task.is_due_window_valid(owner):
                continue

            # Skip tasks that don't fit remaining budget
            if task.duration_minutes > remaining_minutes:
                continue

            # Calculate end time and check against preferred window
            task_end_time = current_time + timedelta(minutes=task.duration_minutes)
            if task_end_time > end_window:
                continue

            # Generate explanation for selection
            reason = f"Selected {task.title} because it is"
            if task.required:
                reason += " required"
            else:
                reason += f" {task.priority}-priority"
            reason += f" and fits within remaining {remaining_minutes} minutes."

            # Add to plan
            schedule_item: ScheduleItem = {
                "task_id": task.task_id,
                "task_title": task.title,
                "duration_minutes": task.duration_minutes,
                "priority": task.priority,
                "start_time": current_time.strftime("%H:%M"),
                "end_time": task_end_time.strftime("%H:%M"),
                "reason": reason,
            }
            self.plan.append(schedule_item)

            # Update state for next iteration
            remaining_minutes -= task.duration_minutes
            current_time = task_end_time

        return self.plan

    def explain_plan(self, owner: Owner, plan: Optional[list[ScheduleItem]] = None) -> list[str]:
        """Return human-readable explanations for plan selection.

        Args:
            plan: Plan items to explain (defaults to self.plan if not provided).
        """
        plan_to_explain = plan if plan is not None else self.plan

        if not plan_to_explain:
            return [
                f"No tasks were selected for {owner.name}. Try increasing daily budget or reducing task durations."
            ]

        explanations = [item["reason"] for item in plan_to_explain]
        return explanations

    def detect_schedule_conflicts(self, pet_plans: dict[str, list[ScheduleItem]]) -> list[str]:
        """Detect overlapping time ranges and return non-fatal warning messages."""
        entries: list[dict[str, str | datetime]] = []

        for pet_name, plan in pet_plans.items():
            for item in plan:
                entries.append(
                    {
                        "pet": pet_name,
                        "task": str(item["task_title"]),
                        "start_str": str(item["start_time"]),
                        "end_str": str(item["end_time"]),
                        "start": _parse_hhmm(str(item["start_time"])),
                        "end": _parse_hhmm(str(item["end_time"])),
                    }
                )

        entries.sort(key=lambda entry: entry["start"])
        warnings: list[str] = []

        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                first = entries[i]
                second = entries[j]

                if second["start"] >= first["end"]:
                    break

                # Overlap check: intervals intersect
                if first["start"] < second["end"] and second["start"] < first["end"]:
                    warnings.append(
                        "⚠️ Conflict: "
                        f"{first['pet']} - {first['task']} ({first['start_str']}-{first['end_str']}) "
                        "overlaps with "
                        f"{second['pet']} - {second['task']} ({second['start_str']}-{second['end_str']})."
                    )

        return warnings
