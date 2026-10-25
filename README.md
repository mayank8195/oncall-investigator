# oncall-investigator

An AI agent that investigates production alerts and reports the likely root cause with its evidence, and a benchmark that measures how often the agent is right.

> **Status: the system runs; the agent does not exist yet.** The services, database, cache and load generator are built and start with one command. Monitoring, the fault injector, the agent and the benchmark come next. This page is updated as each part is added.

## The problem

When a production system breaks, an on-call engineer gets an alert and has to work out which service failed and why, by moving between dashboards, logs and traces. It is slow, it is worst at night, and the symptom often shows up far from the cause.

## What this project builds

1. **A system to investigate.** Three small services (two in Python, one in Java) with Postgres and Redis, instrumented with metrics, logs and traces.
2. **A fault injector.** It breaks that system in ten known ways and records the true cause where the agent can't see it.
3. **An investigator agent.** It starts from an alert, queries the telemetry through read-only tools, and writes a root-cause report with evidence. It is a plain loop with no agent framework, and it runs on more than one model provider.
4. **A benchmark.** Because every fault is injected, the right answer is known. Accuracy, time to root cause and cost per investigation are measured, with confidence intervals.

The work is framed as an engagement with a fictional client, a payments startup called Kinnow Pay. The [discovery document](docs/discovery.md) sets out what the client asked for, what is proposed, and how success is measured.

## What exists today

The system that will be investigated: a small payments backend.

```
load generator -> gateway -> orders -> payments -> Toxiproxy -> mock-bank
                               |  \         |
                             Redis  Postgres-+
```

| Part | What it is |
|---|---|
| [`services/gateway`](services/gateway) | Python, FastAPI. The entry point: checks requests, gives each an ID, calls orders with a time limit |
| [`services/orders`](services/orders) | Python, FastAPI, SQLAlchemy. Products and orders in Postgres, a Redis cache that falls back to the database |
| [`services/payments`](services/payments) | Java 21, Spring Boot. Charges an order through the bank, once, however often it is asked |
| [`services/mock-bank`](services/mock-bank) | Python. A stub for the external bank, reached through Toxiproxy so that it can be made slow or unreachable |
| [`compose/`](compose) | Docker Compose: the services, Postgres, Redis and Toxiproxy |
| [`scripts/seed/`](scripts/seed) | Synthetic data: 200 products, a million orders, 200,000 charges |
| [`loadgen/`](loadgen) | A k6 script that sends steady traffic |
| [`docs/discovery.md`](docs/discovery.md) | The requirements: the problem, constraints, proposed approach, success metrics and risks |

## Run it

You need Docker (with Compose), [uv](https://docs.astral.sh/uv/) and `make`. Java 21 is needed only to run the payments tests outside Docker.

```
make up      # build and start everything, and wait until it is healthy
make seed    # load the synthetic data (about ten seconds)
make smoke   # one order, created and paid, through every service
make load    # two minutes of steady traffic
make down    # stop
```

`make help` lists every command. The gateway listens on `http://127.0.0.1:8000`, with interactive documentation at `/docs`.

To work on the code:

```
make install        # install the Python packages
pre-commit install  # set up the commit checks
make test           # Python and Java tests
```

Work goes on a branch and reaches `main` through a pull request; CI runs the linter, the tests and the image builds on each one.

[`scripts/check_LLM_api.py`](scripts/check_LLM_api.py) checks an Anthropic API key by making one call to the Claude API, for a small fraction of a cent. Put `ANTHROPIC_API_KEY=your-key-here` in a file named `.env` (ignored by git) and run `uv run --env-file .env scripts/check_LLM_api.py`.

## Limitations

- **The environment is simulated.** Faults are known types in a small, clean system, so accuracy here will be higher than on real production incidents.
- **The idea is not new.** Commercial AI tools for incident investigation exist. The value of this project is in the execution and the measurement.
- **The builder designed the faults.** The benchmark may favour failure patterns its author thinks of as typical. Misleading signals, no-fault cases and held-out variants reduce this but don't remove it.
- **It is a learning and portfolio project, not a product.**
