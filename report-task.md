# Engagement Report and Debrief

**Category:** Reporting (manually graded, no flag to submit)

## Brief

During the event your team broke into and held the Northwind Grid hosts (NetOps
Console, MathLab, CacheCTL, BuildHub). Now do what operators do after an
engagement: write it up and brief the owner.

Produce a security assessment report of the hosts your team worked on and present
it to the **system owner**.

## Deliverable

- **A single report as a PDF file.** No other format is accepted.
- Submit the PDF here (or the link, as directed by the organizers) before the deadline.

## What the report must contain

For **each host** your team compromised:

- **Target and access vector** - which host, and how you got in (the entry
  vulnerability, with the request/steps used).
- **Foothold** - which account you landed as.
- **Privilege escalation** - how you went from that account to root.
- **Evidence** - the commands you ran and their output (screenshots or pasted
  terminal), and any flags recovered.
- **Impact** - what an attacker with this access could actually do to the system
  and its data.
- **Remediation** - concrete, actionable fixes the owner should apply.

Plus, for the report as a whole:

- **Executive summary** - a short section the system owner can follow without
  deep technical background: what was found, how bad it is, what to do first.
- **Risk rating** per finding (e.g. Critical / High / Medium / Low) with a one-line
  justification.

## Presentation to the system owner

- Your team will present the report to the **system owner** (the organizers acting
  as the owner).
- The **person presenting must be able to explain every finding in their own words**:
  how the vulnerability works, why it worked on this host, the impact, and how to
  remediate it. "We ran a tool and it returned this" is not sufficient. Expect
  follow-up questions and be ready to answer them.
- Choose a presenter who understands the work - not only who did it.

## Grading (by the judges)

- Technical accuracy and completeness of the findings.
- Clarity and usefulness for the owner (executive summary + remediation).
- The presenter's ability to explain the findings and answer questions.
- Professional structure, readability, and quality of evidence.

## Scope and rules

- Only the four in-scope hosts. Do **not** include the scoring / green-team
  infrastructure or any out-of-scope system in the report.
- This task awards points on the quality of the report and the debrief, judged
  manually. There is no flag to submit here.
