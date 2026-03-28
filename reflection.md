# PawPal+ Project Reflection

## 1. System Design

1. Tracking pet care tasks
2. Get constraints from user
3. Curate a plan based on constraints
**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**Initial Design:**

The PawPal+ system uses four core classes with a single-pet scope:

1. **Owner**: Represents the pet owner with profile and planning constraints.
   - Attributes: `owner_id`, `name`, `daily_time_budget_minutes`, `preferred_start_time`, `preferred_end_time`
   - Responsibilities: manage owner preferences, validate time constraints, check if a given duration fits within budget

2. **Pet**: Represents the pet and manages its associated tasks.
   - Attributes: `pet_id`, `name`, `species`, `age`, `care_notes`, `tasks` (list)
   - Responsibilities: store pet profile, add/remove tasks, retrieve active tasks

3. **Task**: Represents an individual care task with metadata.
   - Attributes: `task_id`, `title`, `category`, `duration_minutes`, `priority`, `required`, `due_by`, `active`
   - Responsibilities: validate task properties (duration > 0, priority ∈ {low, medium, high}), compute priority weight, check if task fits owner's preferred time window, provide summary

4. **Scheduler**: Orchestrates the planning logic; owns all scheduling decisions and reasoning.
   - Attributes: `strategy`, `buffer_minutes`
   - Responsibilities: rank tasks deterministically (required → priority → due_time → duration → title), generate a daily plan that respects time budget and preferred time window, provide explanations for plan selection

**Relationships:**
- Owner → Pet (1:1 aggregation; one owner manages one pet in this scope)
- Pet → Task (1:* composition; tasks belong to the pet)
- Scheduler depends on Owner and Pet for context and uses Task list to produce a plan

**b. Design changes**

- Did your design change during implementation?
Yes
- If yes, describe at least one change and why you made it.

**Design Refinements:**

After reviewing the skeleton, there were five key improvements:

1. **Added ScheduleItem TypedDict** — The initial return type `list[dict]` was vague. I introduced a `ScheduleItem` TypedDict to clearly document the structure of each scheduled item (task_id, task_title, duration_minutes, priority, start_time, end_time, reason). This improves type safety and makes the API contract explicit for UI and test code.

2. **Added Pet → Owner relationship** — Originally, Pet did not reference its Owner. I added an optional `owner` field to Pet so that if needed, Pet can access owner constraints (e.g., to validate task timing). This avoids passing Owner separately to every task validation.

3. **Added validation hooks with `__post_init__`** — The initial skeleton had no validation. I added `__post_init__()` methods to Owner and Task to catch invalid inputs early (e.g., duration ≤ 0, priority not in {low, medium, high}, time format errors). This prevents invalid objects from being created and makes errors fail fast.

4. **Added Scheduler plan caching** — Originally, `Scheduler` had no state and `explain_plan()` required the plan as a parameter. Now `generate_daily_plan()` caches the result in `self.plan`, and `explain_plan()` can optionally reference it. This simplifies the API and reduces coupling between methods.

5. **Added docstrings** — Each class and method now has a docstring describing its purpose and behavior. This aligns with the project's emphasis on clear design documentation.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

My scheduler considers these constraints:

- Owner daily time budget (`daily_time_budget_minutes`)
- Owner preferred planning window (`preferred_start_time` to `preferred_end_time`)
- Task priority (`high`, `medium`, `low`)
- Required vs optional tasks (`required=True` first)
- Task due times (`due_by`) for time-sensitive ordering

I prioritized constraints in this order: required tasks first, then priority, then due time, then duration. I chose this because missing required care (feeding/meds/walks) is higher impact than delaying optional enrichment. After that, due times and shorter durations help create feasible plans within limited time.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

I reviewed my conflict-detection algorithm with AI. A more Pythonic option was a single-pass sweep after sorting (better asymptotic performance), but I kept my current nested-overlap check because it is easier for me to debug and it reports all overlap pairs explicitly in warning messages.

The tradeoff is performance vs. clarity/completeness: my approach is potentially slower on very large schedules, but for this project’s small daily task lists it is reasonable and produces clearer conflict warnings for users.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI in three main ways:

1. **Design brainstorming** for UML class responsibilities and relationships.
2. **Implementation support** for method skeletons, sorting/filtering logic, recurrence handling, and Streamlit state management.
3. **Testing support** to identify high-value happy-path and edge-case tests.

The most helpful prompts were specific and code-aware, for example:
- “Based on this file, what relationships are missing?”
- “How should `Scheduler` retrieve tasks from owner pets?”
- “What edge cases matter most for sorting + recurring tasks?”
- “How can I simplify this algorithm while keeping readability?”

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

One moment was conflict detection. AI suggested a more compact single-pass approach after sorting intervals. I did not accept it immediately because my existing implementation was easier to debug and made overlap reasoning very explicit.

I verified the decision by:
- Running tests for exact-time overlaps and boundary non-overlaps.
- Checking terminal output in `main.py` with intentional conflicts.
- Confirming that warning messages stayed understandable for users.

I kept the clearer version for this project scope, even though the alternative was more optimized.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

I tested core behaviors across all classes:

- Task validation (duration, priority, date/time formats)
- Task completion and recurrence (`once`, `daily`, `weekly`)
- Pet task operations (add/remove/get active)
- Owner constraints and aggregation (`get_all_tasks`)
- Scheduler ranking, time sorting, filtering, and schedule generation
- Conflict detection for overlapping intervals
- Edge cases like empty task lists and non-overlapping boundaries

These tests were important because the scheduler logic depends on many small rules. Unit tests ensured those rules stayed correct as features were added.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I’m highly confident in the current implementation (about **5/5** for the implemented scope) because all automated tests are passing and I validated behavior in both terminal and Streamlit UI.

If I had more time, I would add tests for:
- Time-zone and daylight-saving transitions
- Large task lists (performance and stability)
- Duplicate task IDs and stronger ID lifecycle rules
- Multi-day planning continuity across many recurrences
- More complex due-time conflicts across multiple pets

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I’m most satisfied with turning a simple starter app into a full scheduling system with clear class boundaries, explainable plan output, recurrence handling, and non-fatal conflict warnings. The final UI also reflects backend intelligence instead of being a static form.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

In another iteration, I would:

- Add persistent storage (SQLite or JSON) so data survives app restarts.
- Expand schedule generation from per-pet runs to a global cross-pet planner.
- Improve conflict resolution by suggesting automatic alternatives instead of warnings only.
- Add stronger domain types for times/dates and avoid string-based fields where possible.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

My key takeaway is that AI is most useful when I treat it as a collaborator, not an autopilot: specific prompts + human review + tests produced the best results. Good system design came from iterating between UML, code, and verification rather than trying to get everything right in one pass.
