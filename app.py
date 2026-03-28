import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# === Session state initialization ===
if "owner" not in st.session_state:
    st.session_state.owner = None
    st.session_state.owner_initialized = False
if "pet_counter" not in st.session_state:
    st.session_state.pet_counter = 0
if "task_counter" not in st.session_state:
    st.session_state.task_counter = 0


def get_pet_by_id(owner: Owner, pet_id: str) -> Pet | None:
    """Return the pet with the matching pet_id, or None if not found."""
    for pet in owner.get_pets():
        if pet.pet_id == pet_id:
            return pet
    return None


def get_pet_name_for_task(owner: Owner, task_id: str) -> str:
    """Return the pet name that owns a task id, or 'unknown'."""
    for pet in owner.get_pets():
        for task in pet.tasks:
            if task.task_id == task_id:
                return pet.name
    return "unknown"

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner Setup")
with st.form("owner_form"):
    owner_name = st.text_input("Owner name", value="Jordan")
    daily_budget = st.number_input("Daily time budget (minutes)", min_value=15, max_value=720, value=90)
    start_time = st.text_input("Preferred start (HH:MM)", value="08:00")
    end_time = st.text_input("Preferred end (HH:MM)", value="20:00")
    create_owner = st.form_submit_button("Create / Reset Owner")

if create_owner:
    try:
        st.session_state.owner = Owner(
            owner_id="owner-1",
            name=owner_name,
            daily_time_budget_minutes=int(daily_budget),
            preferred_start_time=start_time,
            preferred_end_time=end_time,
        )
        st.session_state.owner_initialized = True
        st.session_state.pet_counter = 0
        st.session_state.task_counter = 0
        st.success(f"✅ Owner '{owner_name}' is ready.")
        st.rerun()
    except ValueError as exc:
        st.error(f"Could not create owner: {exc}")

if st.session_state.owner_initialized and st.session_state.owner is not None:
    st.markdown("### Pets")
    with st.form("pet_form"):
        pet_name = st.text_input("Pet name", value="Mochi")
        species = st.selectbox("Species", ["dog", "cat", "other"])
        add_pet = st.form_submit_button("Add pet")

    if add_pet:
        st.session_state.pet_counter += 1
        new_pet = Pet(
            pet_id=f"pet-{st.session_state.pet_counter}",
            name=pet_name,
            species=species,
        )
        st.session_state.owner.add_pet(new_pet)
        st.success(f"✅ Added pet '{new_pet.name}'.")
        st.rerun()

    pet_rows = [
        {"pet_id": pet.pet_id, "name": pet.name, "species": pet.species, "task_count": len(pet.tasks)}
        for pet in st.session_state.owner.get_pets()
    ]
    if pet_rows:
        st.table(pet_rows)
    else:
        st.info("Add at least one pet to continue.")

st.markdown("### Tasks")
st.caption("Add tasks to a selected pet using your backend class methods.")

if st.session_state.owner_initialized and st.session_state.owner is not None:
    pets = st.session_state.owner.get_pets()
    if pets:
        scheduler = Scheduler(strategy="priority_first", buffer_minutes=0)
        pet_options = {f"{pet.name} ({pet.species})": pet.pet_id for pet in pets}
        selected_pet_label = st.selectbox("Select pet for task", list(pet_options.keys()))
        selected_pet_id = pet_options[selected_pet_label]
        selected_pet = get_pet_by_id(st.session_state.owner, selected_pet_id)

        with st.form("task_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                task_title = st.text_input("Task title", value="Morning walk")
            with col2:
                duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            with col3:
                priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

            category = st.selectbox("Category", ["walk", "feed", "meds", "enrichment", "grooming", "other"])
            required = st.checkbox("Required task", value=False)
            add_task = st.form_submit_button("Add task")

        if add_task and selected_pet is not None:
            st.session_state.task_counter += 1
            new_task = Task(
                task_id=f"task-{st.session_state.task_counter}",
                title=task_title,
                category=category,
                duration_minutes=int(duration),
                priority=priority,
                required=required,
            )
            selected_pet.add_task(new_task)
            st.success(f"✅ Added task '{new_task.title}' to {selected_pet.name}.")
            st.rerun()

        if selected_pet is not None and selected_pet.tasks:
            st.write(f"Current tasks for {selected_pet.name} (sorted by time):")
            sorted_tasks = scheduler.sort_by_time(selected_pet.tasks)
            st.table(
                [
                    {
                        "task_id": task.task_id,
                        "title": task.title,
                        "category": task.category,
                        "due_by": task.due_by,
                        "duration_minutes": task.duration_minutes,
                        "priority": task.priority,
                        "required": task.required,
                        "completed": task.completed,
                    }
                    for task in sorted_tasks
                ]
            )

            st.markdown("#### Filtered Task View")
            col_a, col_b = st.columns(2)
            with col_a:
                completion_filter = st.selectbox(
                    "Completion filter",
                    ["all", "completed", "incomplete"],
                    key="completion_filter",
                )
            with col_b:
                pet_filter = st.selectbox(
                    "Pet filter",
                    ["all"] + [pet.name for pet in pets],
                    key="pet_filter",
                )

            completed_value = None
            if completion_filter == "completed":
                completed_value = True
            elif completion_filter == "incomplete":
                completed_value = False

            pet_name_value = None if pet_filter == "all" else pet_filter
            filtered_tasks = scheduler.filter_tasks(
                st.session_state.owner,
                completed=completed_value,
                pet_name=pet_name_value,
            )

            if filtered_tasks:
                st.table(
                    [
                        {
                            "task_id": task.task_id,
                            "title": task.title,
                            "pet": get_pet_name_for_task(st.session_state.owner, task.task_id),
                            "due_by": task.due_by,
                            "priority": task.priority,
                            "completed": task.completed,
                        }
                        for task in scheduler.sort_by_time(filtered_tasks)
                    ]
                )
                st.success(f"Showing {len(filtered_tasks)} task(s) with current filters.")
            else:
                st.info("No tasks match the current filters.")
        elif selected_pet is not None:
            st.info(f"No tasks yet for {selected_pet.name}. Add one above.")
    else:
        st.info("Add a pet before adding tasks.")
else:
    st.info("👆 Create an owner first.")

st.divider()

st.subheader("Build Schedule")
st.caption("Generate a daily plan for a selected pet.")

if st.session_state.owner_initialized and st.session_state.owner is not None and st.session_state.owner.get_pets():
    schedule_pet_options = {
        f"{pet.name} ({pet.species})": pet.pet_id for pet in st.session_state.owner.get_pets()
    }
    schedule_pet_label = st.selectbox("Select pet to schedule", list(schedule_pet_options.keys()))
    schedule_pet_id = schedule_pet_options[schedule_pet_label]
    schedule_pet = get_pet_by_id(st.session_state.owner, schedule_pet_id)

    if st.button("Generate schedule"):
        if schedule_pet is None:
            st.error("Could not find selected pet.")
        elif not schedule_pet.get_active_tasks():
            st.warning("⚠️ Please add at least one task before generating a schedule.")
        else:
            try:
                owner = st.session_state.owner
                scheduler = Scheduler(strategy="priority_first", buffer_minutes=0)
                plan = scheduler.generate_daily_plan(owner, schedule_pet)

                # Detect cross-pet conflicts and show non-fatal warnings.
                all_pet_plans = {
                    pet.name: scheduler.generate_daily_plan(owner, pet)
                    for pet in owner.get_pets()
                    if pet.get_active_tasks()
                }
                conflict_warnings = scheduler.detect_schedule_conflicts(all_pet_plans)

                if plan:
                    st.success(f"✅ Daily schedule generated for {schedule_pet.name}!")

                    if conflict_warnings:
                        st.warning(
                            "Scheduling conflicts detected. Review overlapping tasks below and adjust task times or durations."
                        )
                        with st.expander("View conflict details"):
                            for warning in conflict_warnings:
                                st.write(f"- {warning}")
                    else:
                        st.success("No task time conflicts detected across pets.")

                    st.markdown("### Today's Schedule")
                    schedule_data = [
                        {
                            "Time": f"{item['start_time']}-{item['end_time']}",
                            "Task": item["task_title"],
                            "Priority": item["priority"],
                            "Duration": f"{item['duration_minutes']} min",
                        }
                        for item in plan
                    ]
                    st.table(schedule_data)

                    st.markdown("### Why This Schedule")
                    explanations = scheduler.explain_plan(owner, plan)
                    for i, reason in enumerate(explanations, 1):
                        st.write(f"{i}. {reason}")

                    total_scheduled = sum(item["duration_minutes"] for item in plan)
                    st.markdown("---")
                    st.metric("Total Scheduled", f"{total_scheduled} minutes")
                    st.metric(
                        "Remaining Budget",
                        f"{owner.daily_time_budget_minutes - total_scheduled} minutes",
                    )
                else:
                    st.info("No tasks could be scheduled. Try increasing budget or reducing task durations.")
            except Exception as exc:
                st.error(f"❌ Error generating schedule: {exc}")
else:
    st.info("Create an owner and add a pet to generate a schedule.")
