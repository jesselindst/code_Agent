# Agentic Dev Framework

A lightweight library that implements an **agentic coding framework**—designed to behave like a *competent developer*, not an over-eager beginner with Stack Overflow access.

---

## Why

I'm tired of the current state of AI agents. Most feel like junior devs on steroids—great at regurgitating boilerplate, terrible at building long-term context or iterating sensibly.

### Case in Point

I tried building an email app with AI integration using Cursor’s Agent Mode. The first impression? **Amazing**. I provided UI styles, backend framework, and basic functionality—and boom! It worked. Frontend and backend CRUD operations just clicked.

Then came the pain.

I tried adding a few simple features and suddenly the agent:
- Started hallucinating code,
- Forgot prior implementation details,
- Became less helpful with each iteration.

Turns out: **limited context windows kill long-term dev flow**. But humans don’t have the whole codebase memorized either—we remember *where to look*. We use search. We use logs. We document.

We can build that into an LLM.

---

## Core Idea

We build an **agentic workflow** like this:

```
Planning → Implementation → Validation → Iteration
```

With strict structure:
- Limit the agent to a *single feature* per session.
- Force it to write **logfiles** that serve as memory/context for future sessions.
- Enforce a validation loop before moving to the next task.

---

## Current Features

- Minimal agent loop 
- Terminal Tools

---

## Roadmap

- [ ] Implement detailed **planning logs**
- [ ] Add **iteration logs** and versioned memory
- [ ] Refine tool usage—ideally inside a **sandboxed environment**
- [ ] Build a small demo project (maybe a Todo app or Email app reboot)

---

We’re not trying to build a general-purpose agent. We’re building something **opinionated**, useful, and focused. A developer assistant that:
- Respects scope
- Documents well
- Doesn’t try to do everything at once
---

## Contact / Contribute

Open to ideas, contributions, or collaborations. Hit me up with feature suggestions or horror stories of AI dev tools gone rogue.
