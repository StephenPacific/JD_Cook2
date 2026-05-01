# JDcook - Project Vision

I wanted to share a project I have been building recently, because it connects with several ideas from the courses I have taken with you: AI agents, human feedback, local workflows, and trustworthy automation.

The project is called **JDcook**. It is a local-first AI workflow for tailoring resumes to specific job descriptions.

The simple idea is:

> AI can write the first draft, but every claim should be traceable to real user evidence, and every human edit should help the next draft become better.

## Current workflow

User evidence and job description  
-> AI creates a resume draft  
-> Human reviews and edits it  
-> System checks quality and evidence links  
-> Final resume is approved  
-> System records what changed  
-> User chooses useful patterns  
-> Future drafts improve

## What we have built so far

We have already built the first working local version.

The system can take a job description, read the user's local evidence, and generate a tailored resume draft. The important point is that the draft is not treated as free AI-generated text. Each resume bullet keeps an internal evidence marker, so the user can trace the claim back to the original resume material or project note.

We also built a checking step before approval. A validator checks whether the resume is valid, whether it fits within the expected format, whether each bullet has evidence, and whether internal review notes are separated from the public version. If a bullet lacks evidence or the public version would leak internal notes, the workflow is blocked before approval.

After the user edits and approves a resume, the system creates a learning note. This note compares the AI draft with the final human-edited version. The user can then decide what should be learned.

The rule system is separated into three levels:

1. **General rules** - principles that should work for most users and most jobs.
2. **Personal preferences** - the user's own writing style and layout preferences.
3. **Job-specific choices** - decisions that were useful for one job but should not become global rules.

This is important because I do not want the AI to overfit one resume cycle and turn a one-time edit into a permanent rule.

## How we are doing it

The current version is intentionally simple. It is a local workflow rather than a cloud product.

We split the system into a few parts:

1. The user keeps their own evidence locally.
2. Each job description becomes a stable input.
3. The AI reads the job, the evidence, and the rules before drafting.
4. The draft keeps internal evidence links for each claim.
5. A checker catches formatting and evidence-tracking problems before approval.
6. A learning note records the difference between the AI draft and the final version.
7. The user manually decides which lessons should become future rules.

So the AI is not acting as an uncontrolled resume generator. It is one part of a controlled workflow with evidence, checks, and human judgement.

## Why this matters

Many AI resume tools focus on producing polished text quickly. JDcook focuses on a different question:

> Can we make AI-assisted resume writing more truthful, private, and personal over time?

The project is trying to solve three problems:

1. **Truthfulness:** the resume should not invent experience. The current system is not a perfect semantic truth checker yet, but it already forces each bullet to keep an evidence link.
2. **Privacy:** the user's career history stays local by default.
3. **Personalisation:** the system learns from the user's own edits instead of forcing everyone into the same generic resume style.

## What we are testing now

At this stage, I am not trying to build a full web product. I first want to test whether the core loop is actually useful.

The main question is:

> If we run several real resume cycles, will the AI draft need fewer manual edits over time?

The next step is to run more real job cycles and observe:

- whether repeated mistakes decrease
- whether the rule system becomes more useful
- whether the user spends less time editing
- whether the final resumes stay truthful and easy to audit

This gives us a practical evaluation signal: if the same manual corrections become less frequent, unsupported claims are caught earlier, and the rules improve future drafts without overfitting to one job, then the loop is working.

## Possible next stage

Once the core loop is stable, the next stage could add:

1. **Resume quality scoring** - a simple report that highlights weak areas, not a final judgement.
2. **Limited automatic revision** - AI can revise the weakest parts, but only within strict limits.
3. **A simple local dashboard** - a visual way to see job status, resume drafts, final PDFs, and learning notes.

The long-term goal is to turn JDcook into a trustworthy AI career-document workflow: private by default, evidence-based, and improved through human feedback rather than uncontrolled generation.
