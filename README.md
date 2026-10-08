# oncall-investigator

An AI agent that investigates production alerts and reports the likely root cause with its evidence, and a benchmark that measures how often the agent is right.

> **Status: early.** The repository is set up and the requirements are written. The system, the agent and the benchmark are not built yet. This page is updated as each part is added.

## The problem

When a production system breaks, an on-call engineer gets an alert and has to work out which service failed and why, by moving between dashboards, logs and traces. It is slow, it is worst at night, and the symptom often shows up far from the cause.

## What this project builds

1. **A system to investigate.** Three small services (two in Python, one in Java) with Postgres and Redis, instrumented with metrics, logs and traces.
2. **A fault injector.** It breaks that system in ten known ways and records the true cause where the agent can't see it.
3. **An investigator agent.** It starts from an alert, queries the telemetry through read-only tools, and writes a root-cause report with evidence. It is a plain loop with no agent framework, and it runs on more than one model provider.
4. **A benchmark.** Because every fault is injected, the right answer is known. Accuracy, time to root cause and cost per investigation are measured, with confidence intervals.

The work is framed as an engagement with a fictional client, a payments startup called Kinnow Pay. The [discovery document](docs/discovery.md) sets out what the client asked for, what is proposed, and how success is measured.

## What exists today

| File | What it is |
|---|---|
| [`docs/discovery.md`](docs/discovery.md) | The requirements: the problem, constraints, proposed approach, success metrics and risks |
| [`smoke_test.py`](smoke_test.py) | A setup check: one call to the Claude API that prints the answer, the token counts and the cost |

## Check your setup

You need [uv](https://docs.astral.sh/uv/) and an Anthropic API key. Clone the repository, create a file named `.env` in it containing `ANTHROPIC_API_KEY=your-key-here`, then run:

```
uv run --env-file .env smoke_test.py
```

It prints a one-sentence answer with the token counts and the cost of the call, which is a small fraction of a cent. `.env` is ignored by git.

To work on the code, run `pre-commit install` once to set up the commit checks.

## Limitations

- **The environment is simulated.** Faults are known types in a small, clean system, so accuracy here will be higher than on real production incidents.
- **The idea is not new.** Commercial AI tools for incident investigation exist. The value of this project is in the execution and the measurement.
- **The builder designed the faults.** The benchmark may favour failure patterns its author thinks of as typical. Misleading signals, no-fault cases and held-out variants reduce this but don't remove it.
- **It is a learning and portfolio project, not a product.**
