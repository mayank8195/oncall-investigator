# Discovery: incident diagnosis for Kinnow Pay

Kinnow Pay is a fictional client. This document frames the project the way a real engagement would start: with what the client asked for, what they need, and what would count as success.

**Status:** draft after the first call, for review with the client on the second.

## 1. Context

Kinnow Pay is a Bengaluru payments startup with 15 engineers. Its checkout API is used by about 200 small online merchants.

The backend is a set of Python services plus one Java payments service that came with an acquired team. Data lives in Postgres and Redis. Monitoring is Prometheus, Grafana and Loki. Distributed tracing is only partly rolled out, and some older components write nothing but log files.

## 2. What they asked for

> "We want AI to fix our incidents automatically. Our on-call engineers are burning out."
>
> Kinnow Pay's CTO, first call

## 3. The underlying problem

The request sets a clear goal: take load off the on-call engineers. To see where that load comes from, we looked at the details shared on the same call.

| What we were told | What it suggests |
|---|---|
| Two to three incidents a week, shared by a rotation of six | The volume is moderate. Burnout is not coming from the number of incidents alone |
| A median of about 40 minutes to identify the root cause | Most of the time goes on finding the cause, before any fix starts |
| Much longer at night | A tired engineer, alone, with nobody to ask |
| Much longer when the Java service is involved | Only two of the six know that service, so the other four are investigating code they don't understand, or waking one of the two |

So the problem is **time to diagnosis**, and it is worst in two situations: at night, and in the one service most of the rotation doesn't know.

Who it hurts:

- **On-call engineers.** Long, stressful investigations, often at night.
- **The two engineers who know the Java service.** They are effectively on call all the time, because they are the escalation path.
- **Merchants.** Checkout is degraded or down for as long as diagnosis takes.
- **The business.** Lost payments during incidents, and a retention risk among the engineers carrying the load.

What the client needs is for an on-call engineer to get from an alert to a credible root cause, with the evidence for it, in much less than 40 minutes, including when they have never worked on the failing service.

We therefore recommend starting with diagnosis support, as the first stage towards the automation the CTO has in mind. Section 7 sets out where automatic fixing fits in that sequence.

## 4. Current workflow

The first call did not cover this in detail. The steps below are the usual shape for a team with this tooling, and need confirming with an on-call engineer (section 11).

| Step | What happens | Where time is lost |
|---|---|---|
| 1. Alert | A Prometheus alert pages the on-call engineer | Little |
| 2. Orient | The engineer opens a laptop and works out which dashboards apply | Some; more at night |
| 3. Find the failing service | They move between Grafana dashboards. The symptom shows at the checkout API, but the cause is often in a service behind it | A lot |
| 4. Find the cause | They search logs in Loki, look at traces where they exist, and check recent deploys | Most of it. Older components have logs only, and the Java service is unfamiliar to four of the six |
| 5. Escalate | If the Java service is involved, they call one of the two engineers who know it | Waiting, and a second person woken |
| 6. Fix | Restart, roll back or change configuration | Assumed short once the cause is known |
| 7. Write up | Incident notes, the next day | Not on the critical path |

Steps 3 to 5 are where the 40 minutes go, and they are what this project targets. Steps 1, 2, 6 and 7 stay with the engineer.

## 5. Users and stakeholders

| Who | Role | What they care about |
|---|---|---|
| The six on-call engineers | Users | A fast answer they can check for themselves, not one more noisy tool |
| The two engineers who know the Java service | Users, and the people it relieves most | Fewer escalations |
| The CTO | Sponsor; pays for it | Burnout, reliability and cost |
| Whoever owns security and compliance | Can veto | Customer data leaving the environment; anything with production access |
| Whoever runs Prometheus and Loki | Can veto | Extra query load during an incident, when those systems are already busy |
| Merchants | Affected, not users | Checkout staying up |

We have only spoken to the CTO. The two people who can veto have not been identified yet (section 11).

One requirement follows from who the users are. An engineer woken at 3 a.m. will not act on a conclusion they can't verify, so every report has to show its evidence: the queries that were run and what came back.

## 6. Constraints

The first five came from the call. The sixth was not discussed and has to be asked.

| # | Area | Constraint | What it means for the design |
|---|---|---|---|
| 1 | Access | The tool may read telemetry but must never change anything in production | Read-only tools only. This is enforced by which tools exist and what their credentials allow, not by telling the model to behave |
| 2 | Data | No raw customer data may leave their environment. Logs contain merchant IDs, emails and sometimes partial card numbers | Sensitive fields are masked in code, in one place, before anything is sent to a model API. The masking is tested |
| 3 | Load | Investigations must not overload Prometheus or Loki | Limits on the number of queries per investigation, on time ranges and result sizes, and a timeout on every query |
| 4 | Cost | Under $0.25 per investigation | Tokens and cost are recorded for every run. Step and token limits cap the worst case |
| 5 | Operations | It must work at 3 a.m. with nobody around to set it up | The alert itself starts the investigation. Nobody has to launch anything |
| 6 | AI provider | Not yet known | Ask which provider they already use and whether data must stay in a region. Until then, keep the provider replaceable |

Two of these shape what can be proposed:

- **Constraint 1 and the original request.** Fixing incidents automatically means changing production, which constraint 1 rules out. Section 7 proposes how to sequence the two.
- **Constraint 2 and the use of an external model.** Logs are the main evidence, and they contain customer data. Masking sensitive fields before anything is sent is what makes an external model API compatible with this constraint.

## 7. Out of scope, and why

| Not proposed | Why |
|---|---|
| Fixing incidents automatically | Recommended as a later stage; see below |
| Carrying out any action, even with an engineer's approval | The first version only reports. It recommends a next action in text, and a person carries it out |
| Changing how they monitor (more tracing, new dashboards) | The tool has to work with what exists today, including the components that only write logs |
| Self-hosted models | They would remove the data concern, but models small enough to self-host cheaply are much weaker at multi-step investigation. Masking handles the data concern instead. Revisit if the security owner rejects any external model API |
| Replacing the on-call engineer | The report is advice. The engineer decides what to do with it |

**Automatic fixing: a later stage.** Resolving incidents with less human effort is the right long-term direction, and we share that goal. We recommend reaching it in stages, for three reasons:

1. **The read-only constraint.** Fixing means changing production, which the team has asked the tool never to do. Moving to automation would mean revisiting that constraint deliberately, with the security owner involved.
2. **Diagnosis comes first.** An automatic fix can only be as reliable as the diagnosis behind it, and the accuracy of that diagnosis has not been measured yet. Measuring it is the purpose of this first stage.
3. **The risks are uneven.** A mistaken diagnosis, reviewed by an engineer, costs a few minutes. A mistaken automatic action on a payments system, such as restarting the wrong service or rolling back a good deploy, could turn a partial outage into a full one.

The suggested sequence:

1. **Now:** diagnosis support, with accuracy measured.
2. **Next, if accuracy is high:** suggested actions that an engineer approves.
3. **Later:** automation for narrow, reversible actions only.

## 8. Proposed approach

**What gets built.** An investigator that starts when an alert fires. It queries metrics, logs, traces and recent changes through read-only tools, and within minutes produces a report: the likely root cause, the service responsible, the evidence, what was ruled out, a recommended next action for the engineer, and a plain-English summary. When it can't find the cause, it says so and does not guess.

**How it is proven before it goes near production.** Accuracy can't be measured on Kinnow Pay's real incidents: there are only two or three a week, nobody records the true cause in a form that can be scored, and an untested tool shouldn't be pointed at a payments system. So the first stage runs against a replica:

1. **Build a small system shaped like theirs.** Python services, one Java payments service, Postgres, Redis, and the same monitoring stack.
2. **Break it in known ways.** Ten kinds of fault, plus cases with misleading signals and cases where nothing is wrong.
3. **Build the investigator,** with read-only tools and masking of sensitive data.
4. **Measure it.** Because every fault is injected, the true cause is known, so each report can be scored right or wrong.
5. **Report back.** A one-page memo for the CTO with the results and a recommendation.

**What would come next,** if the results justify it: a shadow pilot on real alerts, where reports are posted next to the engineer's own investigation but nobody relies on them, and the two are compared afterwards.

**What this stage does not show.** Faults in a small, clean replica are easier than real production incidents, so accuracy measured here is an upper estimate. The shadow pilot is what tests it against reality.

## 9. Success metric

| What is measured | Baseline | How |
|---|---|---|
| Diagnosis accuracy: the share of incidents where the report names the right service and the right kind of failure | None exists today. The first version of the investigator sets it, and every change is measured against that on the same incidents | A held-out set of injected faults with known causes, reported with 95% confidence intervals |
| Time to root cause | About 40 minutes (the client's own estimate, unverified), plus a person timed on the same test incidents | From the alert firing to the report |
| Cost per investigation | Target: under $0.25 | Tokens recorded on every run |
| Harmful actions | Must be zero | No tool can write. Separately, text planted in logs tries to instruct the investigator, and the share of attempts that succeed is reported |
| False alarms | None | Cases where nothing is wrong; the right answer is "no incident" |

No accuracy target is fixed in advance. The starting point can't be known before it is measured, and a number promised up front invites tuning the system until the number appears. What is promised is an honest baseline and measured improvements, including the changes that turned out not to help.

### What the problem is worth

A rough calculation from the client's own numbers:

- Two to three incidents a week is about 130 a year.
- At 40 minutes each, that is roughly 87 engineer-hours a year spent on diagnosis.
- At the $0.25 target, running the tool on every incident would cost about $33 a year.

Two things follow:

- **Running cost is not the deciding factor.** The model bill is negligible next to the engineering time needed to build and maintain the tool.
- **Engineer-hours alone don't justify it.** 87 hours a year is small. The value has to come from what those 40 minutes cost in other ways: payments lost while checkout is down, and the burnout the CTO opened with.

We don't have either number yet. Section 11 asks for them, because they decide whether this is worth building.

## 10. Risks

| Risk | How it is limited |
|---|---|
| A confident but wrong diagnosis sends the engineer in the wrong direction and costs more time than having no tool | Every conclusion comes with its evidence and a confidence level. "Inconclusive" is an allowed answer. Accuracy is measured before anyone relies on it, including on cases built to mislead |
| Customer data reaches the model provider | Sensitive fields are masked in code before anything is sent. The masking is tested with synthetic sensitive data, and the security owner reviews it |
| Text inside logs manipulates the investigator. Logs can contain text written by outside parties, and a model may treat it as an instruction | The investigator has no tool that can change anything, so the worst outcome is a wrong report. Planted instructions are part of the test set, and the share that succeed is reported |
| Investigations add load to Prometheus and Loki in the middle of an incident | Limits on the number of queries, the time range and the result size, with a timeout on every query |
| Results on the replica don't carry over to production | Stated as an upper estimate from the start. The shadow pilot tests it on real alerts before anyone depends on it |
| Engineers come to trust the reports without checking them | Reports show the evidence and what was ruled out, so checking is quick. Engineers mark each report right or wrong, and accuracy is tracked over time |
| The model provider is unavailable during an incident | The tool is an aid, not a step in the process. Without it, the engineer works exactly as they do today |
| Dependence on one provider's prices or terms | The provider is replaceable by design, and two providers are compared in the measurements |

## 11. Open questions for the next call

**Value**

1. What does an hour of degraded or failed checkout cost, in lost payments and in merchant confidence?
2. Has on-call load contributed to anyone leaving, or asking to come off the rotation?
3. Once the cause is known, how long does the fix usually take?

**Current workflow**

4. Could we walk through two or three recent incidents with the engineers who handled them?
5. Is the 40-minute figure measured or estimated? Are incidents recorded anywhere, with their root cause?
6. What share of incidents involve the Java service, and what share happen at night?
7. Where should a report arrive so that the on-call engineer sees it straight away?

**People**

8. Who owns security and compliance decisions, and can we include them in the next call?
9. Who runs Prometheus and Loki, and what query load would they consider acceptable during an incident?

**Data and AI provider**

10. Which AI providers does Kinnow Pay already use or have agreements with?
11. Are there rules on where data may be processed? Payment data in India is subject to data-localisation requirements; does the team consider that to cover logs, or masked log text?
12. Beyond merchant IDs, emails and card numbers, which fields count as sensitive? Is masked log text acceptable to send to an external model API?

**Technical**

13. Which services have tracing today, and which only write log files?
14. Where are deploys and configuration changes recorded?

## 12. Assumptions

These hold until the questions above are answered. Each one names the question that would confirm or change it.

| # | Assumption | Depends on |
|---|---|---|
| 1 | Diagnosis takes about 40 minutes at the median and is the larger part of the time to resolve an incident | Questions 3 and 5 |
| 2 | The workflow is broadly as described in section 4 | Question 4 |
| 3 | Reducing diagnosis time is valuable enough to justify the build | Questions 1 and 2 |
| 4 | Masked log text may be sent to an external model API | Questions 8, 11 and 12 |
| 5 | There is no required AI provider, so work starts with one and the provider stays replaceable | Question 10 |
| 6 | Alerts already exist and fire reliably. The tool starts from an alert; it does not detect incidents | Question 4 |
| 7 | A replica with Python services, one Java service, Postgres, Redis and the same monitoring stack is close enough to their system for a first measurement | Questions 13 and 14 |
| 8 | Their incidents are mostly common failure types, such as slow queries, exhausted connection pools, a slow third party or a bad deploy | Questions 4 and 6 |
| 9 | The $0.25 target covers model usage per investigation, not the cost of building or hosting the tool | To confirm with the CTO |
