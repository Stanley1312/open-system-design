# Contributing

This repository teaches system design through small, runnable cases. Keep every
contribution easy to enter, easy to run, and focused on one design problem.

## Writing a Case

Start with a concrete problem learners can observe, such as a slow request,
duplicate work, or lost state. Let them experience the problem before
introducing the architecture.

A case should provide:

- a short `README.md` that tells learners where to start;
- a runnable `starter/` with one meaningful first experiment;
- a focused `CHALLENGE.md` containing only the required work;
- a readable reference implementation in `solution/`;
- design notes only when they add useful context or trade-offs.

Do not require UI, deployment, or infrastructure work unless it is central to
the lesson. Introduce one major idea at a time and state intentional shortcuts
clearly. Prefer a small, traceable request flow over unnecessary abstractions.

## Before Submitting

Check that a new learner can run something useful within five minutes. Verify
all commands from a clean checkout and test the main flow, validation, and
important failure cases. Update `README.md` and `CASES.md` when adding or
renaming a case.

Use short Conventional Commit-style subjects such as `feat: add webhook
delivery case` or `docs: explain retry trade-offs`. A pull request should state
the learning goal, what changed, and how it was verified. Include screenshots
only for visible UI changes.
