# Evaluate a taskiq broker other than ZeroMQ

Status: needs-triage
Type: spike

## Problem

`docs/adr/0001-layers-with-fastapi-sqlalchemy-and-taskiq.md` accepts three limits of the ZeroMQ broker until rastro has its first real task. With N workers each task runs N times, a task sent while the worker is down is lost, and no result backend exists. `0001-delete-expired-sessions.md` is a first real task, and it also needs a scheduler, which ZeroMQ does not give.

## Solution

The spike compares the brokers in the [taskiq list of available brokers](https://taskiq-python.github.io/available-components/brokers.html) and recommends one, in an ADR that replaces the ZeroMQ section of ADR 0001.

Redis and NATS are the first candidates, because each one gives a broker, a result backend, and a schedule source from one server.

Acknowledgement is the main criterion. For each candidate, the spike answers:

- When does the broker ack a message: on receive, or after the task ends?
- Does a task whose worker dies in the middle run again, and after what timeout?
- Does a task run more than once with N workers?
- Does a message survive a restart of the broker server?

Kafka's model is the target semantics: a durable log, and a consumer group that commits its offset after the work. Kafka itself is out, because it costs more to run than rastro needs. The spike checks whether NATS JetStream or Redis Streams give the same semantics with one small server.

Deliverables:

- A comparison table of the candidates against the four questions above, with a link to the source code or doc of each answer.
- A prototype that kills a worker in the middle of a task and shows whether the task runs again.
- An ADR with the choice.

## Out of scope

- The migration of `src/rastro/broker.py`, which gets its own ticket after the ADR.
- Kafka and RabbitMQ, unless Redis and NATS both fail the ack questions.

## Acceptance criteria

- [ ] Each candidate answers the four ack questions, with a cited source for each answer.
- [ ] The prototype shows the behaviour of the chosen broker when a worker dies in the middle of a task.

## Open questions

- Is the Redis or NATS integration of taskiq maintained by the taskiq authors or by a third party, and how active is it?
- Does rastro accept at-least-once delivery, so every task must be idempotent?
