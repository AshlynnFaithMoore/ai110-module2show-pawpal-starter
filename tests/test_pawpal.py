"""Tests for the PawPal+ system classes."""

import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


class TestTask:
    """Test the Task class."""

    def test_task_creation_valid(self) -> None:
        """Test creating a valid task."""
        task = Task(
            task_id="t1",
            title="Morning Walk",
            category="walk",
            duration_minutes=30,
            priority="high",
        )
        assert task.title == "Morning Walk"
        assert task.duration_minutes == 30

    def test_task_invalid_duration(self) -> None:
        """Test that zero or negative duration raises ValueError."""
        with pytest.raises(ValueError, match="duration must be greater than 0"):
            Task(
                task_id="t1",
                title="Walk",
                category="walk",
                duration_minutes=0,
                priority="high",
            )

    def test_task_invalid_priority(self) -> None:
        """Test that invalid priority raises ValueError."""
        with pytest.raises(ValueError, match="priority must be one of"):
            Task(
                task_id="t1",
                title="Walk",
                category="walk",
                duration_minutes=30,
                priority="urgent",
            )

    def test_task_priority_weight(self) -> None:
        """Test priority weight mapping."""
        low_task = Task(
            task_id="t1",
            title="Play",
            category="enrichment",
            duration_minutes=20,
            priority="low",
        )
        high_task = Task(
            task_id="t2",
            title="Meds",
            category="meds",
            duration_minutes=5,
            priority="high",
        )
        assert low_task.priority_weight() == 1
        assert high_task.priority_weight() == 3

    def test_task_summary(self) -> None:
        """Test task summary output."""
        task = Task(
            task_id="t1",
            title="Feed",
            category="feed",
            duration_minutes=15,
            priority="medium",
            required=True,
        )
        summary = task.summary()
        assert "Feed" in summary
        assert "15 min" in summary
        assert "required" in summary

    def test_task_mark_complete(self) -> None:
        """Test that mark_complete() changes task completion status."""
        task = Task(
            task_id="t1",
            title="Morning Walk",
            category="walk",
            duration_minutes=30,
            priority="high",
        )
        # Initially not completed
        assert task.completed is False

        # Call mark_complete()
        task.mark_complete()
        assert task.completed is True

        # Call mark_incomplete()
        task.mark_incomplete()
        assert task.completed is False


class TestOwner:
    """Test the Owner class."""

    def test_owner_creation_valid(self) -> None:
        """Test creating a valid owner."""
        owner = Owner(owner_id="o1", name="Jordan")
        assert owner.name == "Jordan"
        assert owner.daily_time_budget_minutes == 60

    def test_owner_invalid_time_budget(self) -> None:
        """Test that zero or negative time budget raises ValueError."""
        with pytest.raises(ValueError, match="budget must be greater than 0"):
            Owner(owner_id="o1", name="Jordan", daily_time_budget_minutes=0)

    def test_owner_invalid_time_format(self) -> None:
        """Test that invalid time format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid time format"):
            Owner(
                owner_id="o1",
                name="Jordan",
                preferred_start_time="25:00",
            )

    def test_owner_invalid_time_window(self) -> None:
        """Test that end time before start time raises ValueError."""
        with pytest.raises(ValueError, match="end time must be after start time"):
            Owner(
                owner_id="o1",
                name="Jordan",
                preferred_start_time="20:00",
                preferred_end_time="08:00",
            )

    def test_owner_set_time_budget(self) -> None:
        """Test updating time budget."""
        owner = Owner(owner_id="o1", name="Jordan")
        owner.set_time_budget(120)
        assert owner.daily_time_budget_minutes == 120

    def test_owner_can_fit(self) -> None:
        """Test checking if tasks fit within budget."""
        owner = Owner(owner_id="o1", name="Jordan", daily_time_budget_minutes=60)
        assert owner.can_fit(30)
        assert owner.can_fit(60)
        assert not owner.can_fit(61)

    def test_owner_add_pet(self) -> None:
        """Test adding a pet to owner."""
        owner = Owner(owner_id="o1", name="Jordan")
        pet = Pet(pet_id="p1", name="Mochi", species="dog")
        owner.add_pet(pet)
        assert len(owner.get_pets()) == 1
        assert pet.owner == owner

    def test_owner_get_all_tasks(self) -> None:
        """Test retrieving all tasks from all pets."""
        owner = Owner(owner_id="o1", name="Jordan", daily_time_budget_minutes=120)
        pet = Pet(pet_id="p1", name="Mochi", species="dog")
        owner.add_pet(pet)

        task1 = Task(
            task_id="t1",
            title="Walk",
            category="walk",
            duration_minutes=20,
            priority="high",
        )
        task2 = Task(
            task_id="t2",
            title="Feed",
            category="feed",
            duration_minutes=10,
            priority="medium",
        )
        pet.add_task(task1)
        pet.add_task(task2)

        all_tasks = owner.get_all_tasks()
        assert len(all_tasks) == 2
        assert task1 in all_tasks
        assert task2 in all_tasks


class TestPet:
    """Test the Pet class."""

    def test_pet_creation_valid(self) -> None:
        """Test creating a valid pet."""
        pet = Pet(pet_id="p1", name="Mochi", species="dog", age=3)
        assert pet.name == "Mochi"
        assert pet.species == "dog"
        assert pet.age == 3

    def test_pet_add_task(self) -> None:
        """Test adding a task to a pet."""
        pet = Pet(pet_id="p1", name="Mochi", species="dog")
        task = Task(
            task_id="t1",
            title="Walk",
            category="walk",
            duration_minutes=20,
            priority="high",
        )
        pet.add_task(task)
        assert len(pet.tasks) == 1
        assert task in pet.tasks

    def test_pet_add_task_increases_count(self) -> None:
        """Test that adding tasks to a pet increases that pet's task count."""
        pet = Pet(pet_id="p1", name="Mochi", species="dog")

        # Initially, pet should have no tasks
        assert len(pet.tasks) == 0

        # Add first task
        task1 = Task(
            task_id="t1",
            title="Morning Walk",
            category="walk",
            duration_minutes=30,
            priority="high",
        )
        pet.add_task(task1)
        assert len(pet.tasks) == 1

        # Add second task
        task2 = Task(
            task_id="t2",
            title="Feed",
            category="feed",
            duration_minutes=15,
            priority="high",
        )
        pet.add_task(task2)
        assert len(pet.tasks) == 2

        # Add third task
        task3 = Task(
            task_id="t3",
            title="Playtime",
            category="enrichment",
            duration_minutes=20,
            priority="medium",
        )
        pet.add_task(task3)
        assert len(pet.tasks) == 3

    def test_pet_remove_task(self) -> None:
        """Test removing a task from a pet."""
        pet = Pet(pet_id="p1", name="Mochi", species="dog")
        task = Task(
            task_id="t1",
            title="Walk",
            category="walk",
            duration_minutes=20,
            priority="high",
        )
        pet.add_task(task)
        assert pet.remove_task("t1")
        assert len(pet.tasks) == 0
        assert not pet.remove_task("t1")  # Already removed

    def test_pet_get_active_tasks(self) -> None:
        """Test retrieving only active tasks."""
        pet = Pet(pet_id="p1", name="Mochi", species="dog")
        active_task = Task(
            task_id="t1",
            title="Walk",
            category="walk",
            duration_minutes=20,
            priority="high",
            active=True,
        )
        inactive_task = Task(
            task_id="t2",
            title="Groom",
            category="grooming",
            duration_minutes=60,
            priority="medium",
            active=False,
        )
        pet.add_task(active_task)
        pet.add_task(inactive_task)

        active_tasks = pet.get_active_tasks()
        assert len(active_tasks) == 1
        assert active_task in active_tasks
        assert inactive_task not in active_tasks


class TestScheduler:
    """Test the Scheduler class."""

    def test_scheduler_rank_tasks_by_priority(self) -> None:
        """Test that tasks are ranked by priority."""
        scheduler = Scheduler()
        low = Task(
            task_id="t1",
            title="Play",
            category="enrichment",
            duration_minutes=20,
            priority="low",
        )
        high = Task(
            task_id="t2",
            title="Meds",
            category="meds",
            duration_minutes=5,
            priority="high",
        )
        ranked = scheduler.rank_tasks([low, high])
        assert ranked[0] == high
        assert ranked[1] == low

    def test_scheduler_rank_tasks_required_first(self) -> None:
        """Test that required tasks rank before optional."""
        scheduler = Scheduler()
        optional = Task(
            task_id="t1",
            title="Play",
            category="enrichment",
            duration_minutes=20,
            priority="high",
            required=False,
        )
        required = Task(
            task_id="t2",
            title="Meds",
            category="meds",
            duration_minutes=5,
            priority="low",
            required=True,
        )
        ranked = scheduler.rank_tasks([optional, required])
        assert ranked[0] == required
        assert ranked[1] == optional

    def test_scheduler_generate_plan_respects_budget(self) -> None:
        """Test that generated plan respects time budget."""
        owner = Owner(owner_id="o1", name="Jordan", daily_time_budget_minutes=60)
        pet = Pet(pet_id="p1", name="Mochi", species="dog")

        walk = Task(
            task_id="t1",
            title="Walk",
            category="walk",
            duration_minutes=30,
            priority="high",
        )
        feed = Task(
            task_id="t2",
            title="Feed",
            category="feed",
            duration_minutes=20,
            priority="medium",
        )
        play = Task(
            task_id="t3",
            title="Play",
            category="enrichment",
            duration_minutes=20,
            priority="low",
        )

        pet.add_task(walk)
        pet.add_task(feed)
        pet.add_task(play)

        scheduler = Scheduler()
        plan = scheduler.generate_daily_plan(owner, pet)

        total_minutes = sum(item["duration_minutes"] for item in plan)
        assert total_minutes <= owner.daily_time_budget_minutes

    def test_scheduler_generate_plan_with_buffer(self) -> None:
        """Test that buffer reduces available time."""
        owner = Owner(owner_id="o1", name="Jordan", daily_time_budget_minutes=100)
        pet = Pet(pet_id="p1", name="Mochi", species="dog")

        for i in range(5):
            pet.add_task(
                Task(
                    task_id=f"t{i}",
                    title=f"Task {i}",
                    category="other",
                    duration_minutes=20,
                    priority="medium",
                )
            )

        scheduler_no_buffer = Scheduler(buffer_minutes=0)
        plan_no_buffer = scheduler_no_buffer.generate_daily_plan(owner, pet)

        scheduler_with_buffer = Scheduler(buffer_minutes=10)
        plan_with_buffer = scheduler_with_buffer.generate_daily_plan(owner, pet)

        # Plan with buffer should have fewer or same tasks
        assert len(plan_with_buffer) <= len(plan_no_buffer)

    def test_scheduler_explain_plan(self) -> None:
        """Test that explanations are generated for tasks."""
        owner = Owner(owner_id="o1", name="Jordan", daily_time_budget_minutes=60)
        pet = Pet(pet_id="p1", name="Mochi", species="dog")

        task = Task(
            task_id="t1",
            title="Walk",
            category="walk",
            duration_minutes=30,
            priority="high",
        )
        pet.add_task(task)

        scheduler = Scheduler()
        plan = scheduler.generate_daily_plan(owner, pet)
        explanations = scheduler.explain_plan(owner, plan)

        assert len(explanations) > 0
        assert "Walk" in explanations[0]

    def test_mark_task_complete_daily_creates_next_occurrence(self) -> None:
        """Test completing a daily task creates the next day's instance."""
        pet = Pet(pet_id="p1", name="Mochi", species="dog")
        task = Task(
            task_id="daily-1",
            title="Daily Walk",
            category="walk",
            duration_minutes=20,
            priority="high",
            frequency="daily",
            due_date="2026-03-28",
            due_by="08:00",
        )
        pet.add_task(task)

        scheduler = Scheduler()
        next_task = scheduler.mark_task_complete(pet, "daily-1")

        assert task.completed is True
        assert task.active is False
        assert next_task is not None
        assert next_task.frequency == "daily"
        assert next_task.due_date == "2026-03-29"
        assert next_task.completed is False
        assert next_task.active is True
        assert len(pet.tasks) == 2

    def test_mark_task_complete_weekly_creates_next_occurrence(self) -> None:
        """Test completing a weekly task creates the next week's instance."""
        pet = Pet(pet_id="p2", name="Whiskers", species="cat")
        task = Task(
            task_id="weekly-1",
            title="Weekly Grooming",
            category="grooming",
            duration_minutes=30,
            priority="medium",
            frequency="weekly",
            due_date="2026-03-28",
            due_by="09:00",
        )
        pet.add_task(task)

        scheduler = Scheduler()
        next_task = scheduler.mark_task_complete(pet, "weekly-1")

        assert next_task is not None
        assert next_task.frequency == "weekly"
        assert next_task.due_date == "2026-04-04"

    def test_mark_task_complete_once_creates_no_new_task(self) -> None:
        """Test completing a one-time task does not create a follow-up task."""
        pet = Pet(pet_id="p3", name="Milo", species="dog")
        task = Task(
            task_id="once-1",
            title="Vet Visit",
            category="meds",
            duration_minutes=45,
            priority="high",
            frequency="once",
            due_date="2026-03-28",
            due_by="10:00",
        )
        pet.add_task(task)

        scheduler = Scheduler()
        next_task = scheduler.mark_task_complete(pet, "once-1")

        assert task.completed is True
        assert task.active is False
        assert next_task is None
        assert len(pet.tasks) == 1
