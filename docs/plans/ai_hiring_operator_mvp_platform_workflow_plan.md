# AI Hiring Operator MVP --- Platform UI & Base Workflow Implementation Plan

> **Owner:** Platform UI + Base Agent Workflow\
> **Project stage:** Hackathon MVP\
> **Purpose of this document:** Give the implementation agent enough
> product, architecture, ownership, scope, and acceptance-test context
> to build the assigned foundation without accidentally expanding into
> the whole product.

------------------------------------------------------------------------

## 1. Project Context

The team is building an **AI Hiring Operator platform**. The product is
not intended to be just another ATS or a chat interface that answers HR
questions. Its direction is to coordinate hiring work across external
providers/tools and execute a defined workflow through agents.

For the hackathon MVP, the team has chosen a deliberately small scope:

-   The platform owns a **fixed, predefined agent workflow**.
-   An **Orchestrator** coordinates the agents and controls the order of
    execution.
-   The initial agent roles are:
    1.  **Filter Agent** --- evaluates candidate profiles against job
        criteria.
    2.  **Interview Agent** --- handles the interview-related step in
        the workflow.
    3.  **Schedule Agent** --- checks/coordinates interview scheduling
        through an integration.
-   A separate teammate is responsible for finding and running
    open-source projects from GitHub to simulate external
    providers/platforms.
-   A separate teammate is responsible for the **product spec and test
    harness**.
-   This implementation assignment is limited to the **platform UI and
    the base workflow/runtime**, plus the interface needed to connect
    that workflow to the integration teammate's provider adapters.
-   The workflow may be optimized later based on the product spec and
    harness results. Do not attempt to build a general-purpose
    autonomous workflow designer for the MVP.

### Product principle

**Every candidate should have a clear next step.** The platform should
make workflow execution and its current state visible, and help
coordinate the process. Hiring decisions remain governed by explicit
criteria and human approval where required.

------------------------------------------------------------------------

## 2. My Assigned Responsibility

Build the minimum foundation that makes the agreed workflow
understandable, executable, observable, and connectable to external
provider integrations.

### In scope

-   A platform UI that displays the workflow and its execution state.
-   A fixed workflow definition for the initial Filter → Interview →
    Schedule path.
-   A base Orchestrator that executes steps in order and passes
    structured outputs between steps.
-   Shared input/output contracts for agents and provider integrations.
-   A provider/integration boundary so the workflow does not depend
    directly on a specific open-source provider implementation.
-   Basic run state, step status, error handling, and execution logs
    that can be shown in the UI.
-   A small end-to-end integration with the provider adapters built by
    the integration teammate.
-   A clear exportable representation of the workflow definition, if
    needed by the team's integration approach.

### Out of scope for this assignment

Do **not** build these unless the team/product spec explicitly asks for
them:

-   A production-grade, dynamically editable visual workflow builder.
-   Arbitrary user-created agents or arbitrary workflow graphs.
-   A general multi-tenant enterprise administration system.
-   A complete ATS or a replacement for every HR system.
-   Real integrations with many commercial providers. The MVP should use
    the selected open-source/simulated providers.
-   Advanced agent memory, cross-company learning, or autonomous model
    fine-tuning.
-   Complex distributed execution, Kubernetes, or a microservice per
    agent.
-   A full observability stack; basic run history and logs are enough
    for the demo.
-   Unreviewed automatic hiring decisions or actions that violate
    configured permissions.

------------------------------------------------------------------------

## 3. Target MVP User Journey

The exact business rules must follow the product spec/harness owner's
final definition. Use this as the initial technical skeleton, not as a
substitute for that spec.

1.  A user opens the platform and selects or starts a demo hiring
    workflow.
2.  The platform loads a job and candidate data from the
    integration/provider layer.
3.  The Orchestrator creates a workflow run and records its initial
    state.
4.  The **Filter Agent** receives the job criteria and candidate data.
    It returns a structured result for each candidate.
5.  The Orchestrator validates the result and passes eligible candidates
    (or the explicitly specified subset) to the **Interview Agent**.
6.  The Interview Agent determines the required interview step and
    returns a structured result.
7.  The Orchestrator passes the required scheduling data to the
    **Schedule Agent**.
8.  The Schedule Agent uses provider tools to check availability and
    propose or create a schedule, according to the integration
    capabilities and product rules.
9.  The platform displays the overall result, each step's status, any
    errors, and any action requiring human attention.

The workflow must be able to represent failure or a blocked state. It
must not falsely display a successful booking if the provider has not
confirmed it.

------------------------------------------------------------------------

## 4. Proposed High-Level Architecture

``` text
┌───────────────────────────────────────────────┐
│                 Platform UI                   │
│ Workflow view · Run status · Candidate results│
│ Step details · Errors · Human-action requests │
└───────────────────────┬───────────────────────┘
                        │ Start run / read run state
┌───────────────────────▼───────────────────────┐
│            Workflow Runtime / API              │
│ Run lifecycle · State · Validation · Logs      │
└───────────────────────┬───────────────────────┘
                        │
┌───────────────────────▼───────────────────────┐
│                  Orchestrator                  │
│ Fixed step order · Context passing · Routing   │
│ Retry/error policy · Status transitions        │
└──────────────┬────────────────┬───────────────┘
               │                │
       ┌───────▼──────┐ ┌───────▼────────┐ ┌────────────────┐
       │ Filter Agent │ │ Interview Agent│ │ Schedule Agent │
       └───────┬──────┘ └───────┬────────┘ └───────┬────────┘
               └────────────────┴──────────────────┘
                                │ tool calls
┌───────────────────────────────▼────────────────┐
│       Provider Adapter / Integration Layer      │
│ Candidate/job data · Interview data · Calendar  │
│ Backed by selected open-source demo providers   │
└────────────────────────────────────────────────┘
```

This is a logical architecture, not a mandate to split everything into
separate deployable services. For the MVP, the UI, workflow runtime,
orchestrator, and agents may live in one application if that is the
simplest reliable implementation.

### Responsibility boundaries

-   **UI:** starts runs and presents state/results. It should not
    contain workflow business logic.
-   **Orchestrator:** controls sequence, passes validated data, updates
    run/step state, and handles failures.
-   **Agent:** performs a specific reasoning/task step and returns a
    structured result. It should not secretly control the whole
    workflow.
-   **Provider adapter:** translates a stable internal contract into the
    API/data model of a selected provider.
-   **Harness:** supplies test scenarios and checks expected behavior.
    Coordinate with the harness owner rather than duplicating their
    work.
-   **Product spec:** is the source of truth for the intended user
    journey, business rules, and success criteria.

------------------------------------------------------------------------

## 5. Workflow and Agent Contracts

Use explicit contracts between steps. Avoid passing large, unstructured
prompt text as the only interface between agents.

### 5.1 Common agent result

A suggested common envelope:

``` json
{
  "status": "success",
  "data": {},
  "summary": "Short human-readable explanation",
  "warnings": [],
  "error": null,
  "requires_human_action": false
}
```

Suggested status values:

-   `success` --- step completed and output is valid.
-   `needs_human` --- the step requires a human decision or approval.
-   `blocked` --- cannot continue until an external condition is
    resolved.
-   `failed` --- step failed after the allowed handling/retry policy.

These are proposed MVP conventions. Align names and schemas with the
product spec/harness owner before freezing them.

### 5.2 Workflow run

Each run should have at least:

-   `run_id`
-   `workflow_id` and/or `workflow_version`
-   `status`
-   `started_at`, `updated_at`, and optional `completed_at`
-   current step
-   input/reference to job and candidate data
-   step results
-   errors/warnings
-   human-action requirement, if any

### 5.3 Step execution record

Each step should record at least:

-   `step_id` and agent name
-   status
-   start/end timestamps
-   input summary or safe reference
-   structured output or safe reference
-   error details if it failed
-   provider/tool calls made, where useful for debugging

Do not log secrets, credentials, or unnecessary personal data.

### 5.4 Initial fixed workflow

Keep the MVP workflow simple and explicit:

``` text
START
  ↓
LOAD_JOB_AND_CANDIDATES
  ↓
FILTER_AGENT
  ↓
VALIDATE_FILTER_RESULT
  ↓
INTERVIEW_AGENT
  ↓
VALIDATE_INTERVIEW_RESULT
  ↓
SCHEDULE_AGENT
  ↓
VALIDATE_SCHEDULING_RESULT
  ↓
COMPLETED / NEEDS_HUMAN / BLOCKED / FAILED
```

Implement only branches required by the agreed product spec. For
example, if no candidate passes filtering, the workflow should end with
a clear result instead of attempting to schedule an interview.

------------------------------------------------------------------------

## 6. Provider Integration Boundary

The integration teammate owns selecting and running the open-source
provider projects. My responsibility is to make the workflow connect to
them through a stable interface.

### Required collaboration

Agree on these details early:

1.  Which open-source project(s) will simulate the provider environment?
2.  How will the project be run locally (Docker Compose, local process,
    or other)?
3.  Which APIs or data interfaces are available?
4.  How are demo data and reset/seed operations handled?
5.  Which provider actions are read-only and which mutate data?
6.  What authentication, base URLs, ports, and environment variables are
    required?
7.  What is the expected success/error response for each operation?

### Adapter design

Agents should call an internal interface, not hardcode a provider URL
throughout the workflow.

Possible logical interfaces (rename to match the selected provider and
language):

``` text
HiringDataProvider
  - getJob(jobId)
  - listCandidates(jobId)
  - getCandidate(candidateId)

InterviewProvider
  - getInterviewContext(candidateId, jobId)

SchedulingProvider
  - getAvailability(interviewerId, timeRange)
  - createInterviewSchedule(request)
  - getSchedule(scheduleId)
```

These are examples, not a demand to implement every method. Implement
only the operations required by the MVP journey and actually supported
by the chosen open-source project.

### Integration rules

-   Keep provider-specific request/response mapping inside adapters.
-   Normalize provider data into the platform's internal schema.
-   Set API base URLs and credentials through environment
    variables/configuration.
-   Return explicit errors when the provider is unavailable or rejects
    an action.
-   Never claim an external action succeeded until the provider confirms
    it.
-   Avoid duplicate bookings or other duplicate mutations on retries.
    Use an idempotency key if supported; otherwise define a safe
    check-before-create strategy.
-   Use mock responses only for local development or tests, and label
    them clearly. The final demo should exercise the agreed integration
    path.

------------------------------------------------------------------------

## 7. Platform UI --- Minimum Screens/Components

Keep the UI focused on proving the workflow works.

### A. Workflow overview

Display:

-   workflow name and brief description
-   fixed sequence of agents/steps
-   a **Run workflow** action
-   current run status

The MVP does not require a drag-and-drop workflow editor.

### B. Run progress

Display the steps in order with clear statuses:

-   Pending
-   Running
-   Succeeded
-   Needs human action
-   Blocked
-   Failed
-   Skipped

Use the final agreed enum/labels consistently across backend and
frontend.

### C. Run details

Display:

-   job and candidate references
-   each agent's summary and structured result
-   scheduling outcome, if applicable
-   errors/warnings
-   whether a human must intervene
-   timestamps and relevant tool/provider call outcomes

### D. Result view

A recruiter should be able to understand:

-   what happened to the candidates in this run
-   which workflow step completed or stopped
-   what action was taken (or not taken)
-   what needs to happen next

Do not expose raw prompts or sensitive credentials. Provide useful
summaries and safe, structured diagnostics instead.

------------------------------------------------------------------------

## 8. Implementation Phases

Work in small, verifiable increments. Do not start by building a large
abstraction framework.

### Phase 0 --- Confirm the interface with teammates

-   [ ] Read the latest product spec and acceptance criteria.
-   [ ] Agree with the integration teammate on the provider project and
    its available APIs.
-   [ ] Agree with the harness teammate on workflow input/output and
    expected test cases.
-   [ ] Confirm the team's language/framework and repository
    conventions.
-   [ ] Write down the contract and environment variables before wiring
    the full flow.

**Exit criteria:** The team agrees on one demo journey, one initial
provider path, and the minimum data contracts.

### Phase 1 --- Create the UI shell

-   [ ] Build the platform page/layout.
-   [ ] Show the fixed workflow steps.
-   [ ] Add a run-start control.
-   [ ] Add a run-progress/status view.
-   [ ] Add a run-details/result area.
-   [ ] Use temporary fixture data only until the runtime API is
    available.

**Exit criteria:** The UI can display a representative workflow run
without implementing fake business logic in the frontend.

### Phase 2 --- Define the workflow and contracts

-   [ ] Define workflow ID/version and the fixed step list.
-   [ ] Define run and step status enums.
-   [ ] Define each agent's input/output schema.
-   [ ] Define validation for each step output.
-   [ ] Define what happens when filtering returns no candidates.
-   [ ] Define failure, blocked, and human-action states.

**Exit criteria:** The workflow can be tested with deterministic
fixtures and each transition has a clear expected outcome.

### Phase 3 --- Implement the base Orchestrator

-   [ ] Start a run and assign a unique run ID.
-   [ ] Execute steps in the agreed order.
-   [ ] Pass validated structured output to the next step.
-   [ ] Record step status, timestamps, summaries, and errors.
-   [ ] Stop or branch safely when a step fails or requires human
    action.
-   [ ] Prevent the UI from reporting success before the run is
    complete.
-   [ ] Add basic retry/timeout handling only where appropriate.

**Exit criteria:** A test run can traverse the fixed flow and show
correct states for both success and failure scenarios.

### Phase 4 --- Connect the provider adapters

-   [ ] Add the agreed internal provider interface.
-   [ ] Implement the adapter for the open-source project selected by
    the integration teammate.
-   [ ] Configure URLs and credentials through environment variables.
-   [ ] Map provider data into internal schemas.
-   [ ] Test provider unavailable, invalid response, and rejected
    mutation cases.
-   [ ] Verify scheduling success only after confirmation from the
    provider.

**Exit criteria:** At least one complete demo journey uses the real
selected integration path rather than only frontend fixtures.

### Phase 5 --- Connect the UI to runtime

-   [ ] Replace fixture data with runtime API calls.
-   [ ] Start workflow runs from the UI.
-   [ ] Load run status and details from the runtime.
-   [ ] Reflect step transitions and errors in the UI.
-   [ ] Add loading, empty, and failure states.
-   [ ] Ensure refresh/reopen does not silently lose the displayed run
    state.

**Exit criteria:** A user can trigger a run and understand its progress
and outcome from the platform UI.

### Phase 6 --- Verify with the harness and prepare the demo

-   [ ] Run the happy-path scenario.
-   [ ] Run a no-candidate scenario.
-   [ ] Run a provider-unavailable scenario.
-   [ ] Run a scheduling failure/rejection scenario.
-   [ ] Run a `needs_human`/blocked scenario if required by the product
    spec.
-   [ ] Fix discrepancies between actual behavior and harness
    expectations.
-   [ ] Document how to start the platform and provider environment.
-   [ ] Prepare seeded demo data and a reliable reset procedure.

**Exit criteria:** The team can repeat the demo from a clean state and
explain what happened at every step.

------------------------------------------------------------------------

## 9. Definition of Done

The base implementation is ready for the MVP when all of the following
are true:

-   [ ] The UI displays the fixed workflow and can start a run.
-   [ ] The Orchestrator executes Filter → Interview → Schedule in the
    agreed order.
-   [ ] Each agent has a documented input/output contract.
-   [ ] Agent outputs are validated before they are passed downstream.
-   [ ] Run and step statuses are recorded and visible.
-   [ ] Failures are explicit and do not masquerade as success.
-   [ ] The workflow calls the selected open-source provider through an
    adapter.
-   [ ] Provider-specific details are not scattered through
    agent/workflow logic.
-   [ ] Scheduling or other mutations are shown as successful only after
    provider confirmation.
-   [ ] At least the agreed happy path and key failure paths pass the
    harness.
-   [ ] A teammate can run the demo using the documented setup
    instructions.

------------------------------------------------------------------------

## 10. Risks and Design Guardrails

### Do not overbuild

This is a hackathon MVP. A fixed, understandable workflow is preferable
to a generic workflow platform that cannot be demonstrated reliably.

### Do not equate "multi-agent" with "multiple microservices"

The agents can initially be modules/functions/classes in one
application. Split them into separate services only if there is a
demonstrated need.

### Do not make the UI the source of truth

The backend/runtime should own workflow state. The UI renders state
returned by the runtime.

### Do not let agents freely invoke arbitrary tools

Each agent should have an explicit allowlist of tools. Provider
mutations should be validated, and actions requiring human approval must
pause instead of proceeding.

### Make execution inspectable

For the demo, it must be possible to tell which step ran, what
input/output it used (in a safe summarized form), whether a provider was
called, and why the workflow stopped.

### Keep the future optimization path open

Later improvements may change prompts, models, routing, retry behavior,
or step logic based on product-spec and harness results. Avoid coupling
the workflow to one provider or burying business rules in UI code.

------------------------------------------------------------------------

## 11. Important Decisions to Confirm --- Do Not Guess

The implementation agent should inspect the repository and ask the team
or record assumptions before making major choices about:

-   frontend framework and UI component library
-   backend language/framework
-   whether the workflow runs in the same application or a separate
    runtime
-   the provider open-source project(s), APIs, and local setup
-   exact job/candidate/interview schema
-   exact Filter, Interview, and Schedule Agent responsibilities
-   model/LLM provider and whether each step needs an LLM at all
-   persistence requirement for run history
-   authentication requirements for the hackathon demo
-   export format and target runtime, if workflow export is actually
    required
-   exact harness cases and acceptance criteria

Prefer the simplest choice consistent with the existing repository and
teammates' interfaces. Do not introduce a new framework or
infrastructure solely for hypothetical future scale.

------------------------------------------------------------------------

## 12. Handoff Prompt for the Coding Agent

You are implementing the **Platform UI + Base Agent Workflow** portion
of the AI Hiring Operator hackathon MVP.

First inspect the existing repository, conventions, dependencies, and
any current product spec. Do not assume the repository is empty or
replace existing code without understanding it.

Your job is to deliver a small, working foundation:

1.  Build the platform UI for the fixed workflow and run status.
2.  Implement a base Orchestrator that executes Filter Agent → Interview
    Agent → Schedule Agent.
3.  Define explicit, validated input/output contracts and run/step
    states.
4.  Integrate through a provider-adapter boundary agreed with the
    integration teammate.
5.  Connect the UI to runtime state.
6.  Verify behavior against the product spec and harness.

Follow these rules:

-   Keep the MVP fixed-flow and small.
-   Reuse the project's existing stack and conventions.
-   Do not invent provider APIs; inspect the chosen open-source project
    and coordinate with its owner.
-   Do not invent business rules; follow the product spec, and clearly
    mark unresolved assumptions.
-   Do not claim an external action succeeded without provider
    confirmation.
-   Make failure, blocked, and human-action states explicit.
-   Keep secrets in environment configuration, not source code.
-   Add tests for workflow transitions, contract validation, and
    integration failure cases.
-   Before broad refactors or adding major dependencies, explain why
    they are necessary.
-   Implement incrementally and report files changed, commands run, test
    results, remaining assumptions, and the next recommended step.

**First action:** inspect the repository and report the existing stack,
entry points, current state, and the smallest implementation sequence.
Then proceed in small changes with verification after each meaningful
step.
