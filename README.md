# w1j0y-workflow
What: The front page of a small, working example of an AI-assisted web security testing workflow built on Claude Code.
Who writes: The author. In your copy, you.
Who reads: You, first.
Wired into: GETTING_STARTED.md, STRUCTURE.md, GLOSSARY.md, ETHICS.md, AGENTS.md

The companion repo to the video series [playlist link]. It is a house for one idea: a testing workflow in which every prompt, rule, gate and note is a plain file, and every file says what it is wired into.

## What is in it

- Rules for the agent (`AGENTS.md`) and the limits you work inside (`ETHICS.md`).
- Prompts for each phase of a web assessment, run by an orchestrator that uses fresh subagents and refuses to move on until a script passes.
- Small tools in Python and shell: a ledger gate, a scope checker, a hook that checks Burp and Chrome tool calls against scope, a recon wrapper, a wiring check, a secret scan. They use the standard library only.
- Starter technique files, a memory layout, and templates plus generator prompts so you can build your own version from your own resources.
- One invented example program, "Example Shop Bounty", with `.test` hosts, so you can see the shape of every file without a real target.

It contains no real targets and no attack strings.

## The one idea

Building the pieces is easy. Keeping them coherent, so that a change in one file is felt in the right other files, is the hard part. Every file starts with a four-line box: what it is, who writes it, who reads it, what it is wired into. A script checks the boxes both ways.

## Who this is for

You can set up a Linux machine or VM and you know the basics of web assessments. Agents, prompts, gates and every file here are explained from the start in `GLOSSARY.md` and the episodes.

## How to use it

1. Read `ETHICS.md`. It is short and binding.
2. Follow `GETTING_STARTED.md` to get a working copy and run the tests.
3. Read `STRUCTURE.md`, the map of every file.
4. Watch an episode, open the files it names, copy the prompt from its description into Claude Code, and build your own version in your own folder.

## Safety

Test only what you are authorized to test. Program rules (automation, AI use, rate limit, identification header) bind you and the agent; the tools read them from the scope file and refuse when they are missing or unconfirmed. The hook is a backstop and has limits that `docs/TOOL_WIRING.md` states plainly. Use test accounts and a separate browser profile.

Repo link: [repo link]
