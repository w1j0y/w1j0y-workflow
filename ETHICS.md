# Ethics and limits
What: The limits this repo works inside: who and what you may test, and the program rules that bind.
Who writes: The author of the series. Change it only to be stricter.
Who reads: You, before the first request. AGENTS.md points the agent at it.
Wired into: README.md, AGENTS.md, GETTING_STARTED.md

1. **Only test what you are allowed to test.** Written permission comes first: a bug bounty program that lists the asset as in scope, a client who signed an agreement, or a lab you run yourself.
2. **Read the program's rules before the first request.** If they are unclear, ask the program or do not test.
3. **Never touch other people's accounts or data.** Use accounts you created. Test accounts only. If a flaw reaches someone else's data, stop and report it.
4. **Keep the footprint small.** Stop at the first sign of a service struggling.
5. **Write down what you did.** A log of every request protects you.
6. **Report responsibly.** Give the owner time to fix it.
7. **Program rules bind you and the agent.** Automation: if the program prohibits automated tools, do not run this workflow against it. AI use: if the program prohibits or restricts AI, do not use it; if it requires disclosure, disclose in the report. Rate: stay at or under the stated limit. Identification header: send the one the program names, with its exact value; if the program names none, send none and never invent one.
8. **A human confirms the rules.** The tools refuse to start a live phase until a person has read the four rules and their quoted source text and confirmed them.
9. **Do not use a real program for practice in a video or a demo.** Practice on an application you run yourself, or on a training platform that invites testing.
10. **Keep secrets out of files.** Tokens, cookies and credentials never go into the ledger, evidence, memory, reports or commits.

## Where to practice

Run an intentionally vulnerable practice application on your own computer, or use a training platform that invites testing. The example data in this repo uses only `.test` names, which are reserved and never resolve on the public internet.

## Limits of the tools

The scope check compares the host a request points at. It cannot see what a page does after a click, a redirect or a script. The tools are a backstop for a careful person, not a substitute for one.
