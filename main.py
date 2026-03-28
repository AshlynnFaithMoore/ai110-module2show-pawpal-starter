"""Main testing script to verify PawPal+ system logic."""

from pawpal_system import Owner, Pet, Task, Scheduler


def main() -> None:
    """Create sample data and generate a daily schedule."""

    # Create an owner with time constraints
    owner = Owner(
        owner_id="owner-1",
        name="Jordan",
        daily_time_budget_minutes=120,
        preferred_start_time="08:00",
        preferred_end_time="18:00",
    )

    # Create two pets
    mochi = Pet(
        pet_id="pet-1",
        name="Mochi",
        species="dog",
        age=3,
        care_notes="Energetic Golden Retriever",
    )
    whiskers = Pet(
        pet_id="pet-2",
        name="Whiskers",
        species="cat",
        age=5,
        care_notes="Indoor cat, prefers quiet",
    )

    # Add pets to owner
    owner.add_pet(mochi)
    owner.add_pet(whiskers)

    # Add tasks for Mochi (dog)
    mochi.add_task(
        Task(
            task_id="t1",
            title="Morning Walk",
            category="walk",
            duration_minutes=30,
            priority="high",
            required=True,
            due_by="08:30",
        )
    )
    mochi.add_task(
        Task(
            task_id="t2",
            title="Feed Breakfast",
            category="feed",
            duration_minutes=10,
            priority="high",
            frequency="daily",
            due_date="2026-03-28",
            required=True,
            due_by="08:00",
        )
    )
    mochi.add_task(
        Task(
            task_id="t3",
            title="Playtime",
            category="enrichment",
            duration_minutes=20,
            priority="medium",
            required=False,
            due_by="12:30",
        )
    )
    mochi.add_task(
        Task(
            task_id="t4",
            title="Afternoon Walk",
            category="walk",
            duration_minutes=30,
            priority="high",
            required=True,
            due_by="14:00",
        )
    )

    # Add tasks for Whiskers (cat)
    whiskers.add_task(
        Task(
            task_id="t5",
            title="Feed Breakfast",
            category="feed",
            duration_minutes=10,
            priority="high",
            required=True,
            due_by="08:00",
        )
    )
    whiskers.add_task(
        Task(
            task_id="t6",
            title="Litter Box Cleaning",
            category="grooming",
            duration_minutes=10,
            priority="medium",
            frequency="weekly",
            due_date="2026-03-28",
            required=True,
            due_by="08:15",
        )
    )
    whiskers.add_task(
        Task(
            task_id="t7",
            title="Playtime (laser)",
            category="enrichment",
            duration_minutes=15,
            priority="low",
            required=False,
            due_by="09:40",
        )
    )

    # Mark one task complete to test completion filtering
    mochi.tasks[1].mark_complete()  # Feed Breakfast complete

    # Create scheduler and generate plans
    scheduler = Scheduler(strategy="priority_first", buffer_minutes=0)

    # Pre-generate plans for each pet so we can detect conflicts across pets.
    plans_by_pet = {pet.name: scheduler.generate_daily_plan(owner, pet) for pet in owner.get_pets()}

    # Conflict detection demo: we intentionally have tasks at the same time across pets.
    print("\n" + "=" * 70)
    print("CONFLICT DETECTION DEMO".center(70))
    print("=" * 70)
    conflict_warnings = scheduler.detect_schedule_conflicts(plans_by_pet)
    if conflict_warnings:
        for warning in conflict_warnings:
            print(warning)
    else:
        print("No schedule conflicts detected.")

    # Demonstrate sorting by HH:MM due_by time
    print("\n" + "=" * 70)
    print("SORTING DEMO (tasks added out of order, then sorted by due_by)".center(70))
    print("=" * 70)
    for pet in owner.get_pets():
        print(f"\n{pet.name} - raw order:")
        for task in pet.tasks:
            print(f"  {task.title:<24} due_by={task.due_by} completed={task.completed}")

        print(f"{pet.name} - sorted by time:")
        for task in scheduler.sort_by_time(pet.tasks):
            print(f"  {task.title:<24} due_by={task.due_by} completed={task.completed}")

    # Demonstrate filtering by completion status and pet name
    print("\n" + "=" * 70)
    print("FILTERING DEMO".center(70))
    print("=" * 70)
    completed_tasks = scheduler.filter_tasks(owner, completed=True)
    print("Completed tasks across all pets:")
    for task in completed_tasks:
        print(f"  - {task.title} ({task.task_id})")

    whiskers_tasks = scheduler.filter_tasks(owner, pet_name="Whiskers")
    print("\nAll tasks for pet name 'Whiskers':")
    for task in whiskers_tasks:
        print(f"  - {task.title} due_by={task.due_by} completed={task.completed}")

    # Demonstrate recurring completion logic
    print("\n" + "=" * 70)
    print("RECURRING COMPLETION DEMO".center(70))
    print("=" * 70)

    next_daily = scheduler.mark_task_complete(mochi, "t2")
    print("Completed Mochi task 't2' (daily).")
    if next_daily is not None:
        print(
            f"  Auto-created next daily task: {next_daily.task_id} due_date={next_daily.due_date} due_by={next_daily.due_by}"
        )

    next_weekly = scheduler.mark_task_complete(whiskers, "t6")
    print("Completed Whiskers task 't6' (weekly).")
    if next_weekly is not None:
        print(
            f"  Auto-created next weekly task: {next_weekly.task_id} due_date={next_weekly.due_date} due_by={next_weekly.due_by}"
        )

    print("=" * 70)
    print("🐾 PawPal+ DAILY SCHEDULE 🐾".center(70))
    print("=" * 70)
    print()

    # Print owner info
    print(f"Owner: {owner.name}")
    print(f"Daily Time Budget: {owner.daily_time_budget_minutes} minutes")
    print(f"Preferred Window: {owner.preferred_start_time} - {owner.preferred_end_time}")
    print()

    # Generate and display schedule for each pet
    for pet in owner.get_pets():
        print(f"\n{'─' * 70}")
        print(f"📌 {pet.name.upper()} ({pet.species.capitalize()})")
        print(f"{'─' * 70}")

        # Get active tasks for display
        active_tasks = pet.get_active_tasks()
        print(f"Total Tasks: {len(active_tasks)}")
        print()

        # Reuse pre-generated plan
        plan = plans_by_pet[pet.name]

        if not plan:
            print("❌ No tasks could be scheduled.")
            print()
            continue

        # Print schedule table
        print(f"{'Time':<12} {'Task':<25} {'Priority':<10} {'Duration':<10}")
        print("─" * 70)

        for item in plan:
            print(
                f"{item['start_time']}-{item['end_time']:<5} {item['task_title']:<25} "
                f"{item['priority']:<10} {item['duration_minutes']} min"
            )

        print()

        # Print explanations with better formatting
        explanations = scheduler.explain_plan(owner, plan)
        print("Why this schedule:")
        for i, reason in enumerate(explanations, 1):
            # Wrap text to 70 chars for readability
            wrapped = []
            words = reason.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 65:
                    current_line += word + " "
                else:
                    if current_line:
                        wrapped.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                wrapped.append(current_line.strip())
            
            for j, line in enumerate(wrapped):
                if j == 0:
                    print(f"  {i}. {line}")
                else:
                    print(f"     {line}")

        # Summary stats
        total_scheduled = sum(item["duration_minutes"] for item in plan)
        print()
        print(f"Total Scheduled: {total_scheduled} minutes")
        print(f"Remaining Budget: {owner.daily_time_budget_minutes - total_scheduled} minutes")

    print()
    print("=" * 70)
    print("✅ Schedule generation complete!".center(70))
    print("=" * 70)


if __name__ == "__main__":
    main()
