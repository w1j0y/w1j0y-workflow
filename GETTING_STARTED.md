# Getting started
What: The steps from nothing to a working copy of this repo, passing tests and a first Claude Code session.
Who writes: The author. In your copy, you.
Who reads: You, once, at the start.
Wired into: README.md, STRUCTURE.md, docs/TOOLS_NEEDED.md, docs/TOOL_WIRING.md, ETHICS.md

1. **A machine.** Use a Linux machine or a virtual machine you set up yourself. Install git, curl, jq and Python 3.10 or newer from your system package manager. Setting up the machine is not covered here.
2. **Read the rules.** Open `ETHICS.md`. If you cannot agree to it, stop here.
3. **Install Claude Code.** Use the install steps on its official documentation page, then run `claude --version` and see a version number. Log in with an account made for this work. Check the page for which plans include which features; this repo does not store keys.
4. **Get the repo.** Run `git clone [repo link]` and change into the folder. For the series, keep this clone for reading and run every prompt in your own working copy: `git clone w1j0y-workflow my-workflow` (use the name of the folder you just cloned), then work inside `my-workflow`.
5. **Run the tests.** Run `bash tools/tests/run.sh`. All tests pass offline. This proves the gate, the scope checker and the hook work on your machine before any tool touches a network.
6. **Run the wiring check.** Run `python3 tools/wiring_check.py`. It prints nothing but a pass line when every file is wired.
7. **First prompt.** Start `claude` in the folder and send: Read AGENTS.md and STRUCTURE.md, then tell me in ten lines what this repo does and what you would refuse to do. Do not change any file.
8. **Read the map.** Open `STRUCTURE.md` and follow the episodes in order. Each names the files it builds and its description holds the prompts to copy.

## If a reply is stopped

Security text can make a model provider's safety systems stop a reply. You may see a message that the response was stopped, or an answer that only asks what to do next. This repo cannot change that. Send the prompt again; if it keeps happening, add one sentence saying that this is the invented practice program whose hosts end in .test. Nothing from a stopped reply counts as done: look at the files before you go on.

## Later, when you reach live testing

- Install the external tools listed in `docs/TOOLS_NEEDED.md`.
- Wire Burp and Chrome with `docs/TOOL_WIRING.md`. Do this only for a program that has authorized you, and only with test accounts.
- Practice first on an intentionally vulnerable application that you run on your own computer.
