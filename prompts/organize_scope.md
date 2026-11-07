# Organize a raw program scope
What: The prompt that turns one raw pasted program page into five consistent scope files, including the four program rules.
Who writes: The repo author. Sanitized from an earlier working prompt.
Who reads: scripts/organize_scope_claude.sh sends it to Claude Code with a task block appended.
Wired into: scripts/organize_scope_claude.sh, scripts/lib/organize_scope_common.sh, tools/validate_scope.py (one-way: script owned by another part), prompts/README.md, STRUCTURE.md

## Goal

Turn one raw pasted bug bounty program page into five consistent target files that `tools/recon.py` and later phases consume. This is an offline organization task: no recon, scanning, HTTP requests, DNS queries or other network activity, and no edits to any tool.

The launcher appends a Task parameters block to this prompt with the absolute raw file path, the target directory, the repo-relative `source_file` value, the scope.json path for the README command, and the validator command. Use those values verbatim. Do not guess paths and do not run from another directory.

## Programs differ: do not assume a layout

Every program structures its page differently: tables, prose, nested headings, per-tier lists, footnotes, changelogs, an appended machine-readable block, or almost nothing. Do not assume any heading, section or tier name exists. Map what the source actually contains onto the schemas below. A category the source does not mention stays empty and is named in `absent_in_source`. A category the source mentions must be filled. Never invent a section to match a template.

## Required behavior

1. Read the entire raw file before writing anything: tables, footnotes, notes after tables, known issues, changelog text, exclusions, safe-harbor and disclosure text, and any appended machine-readable summary. Read it in chunks if it is long. Page chrome (navigation, statistics) may be skipped only after confirming it carries no scope or rule.
2. Use the target directory and `source_file` from the Task parameters. Platform: from the path or the text, otherwise `unknown`. Target name: the directory name unless the source names the program more clearly.
3. Create or overwrite exactly these files in the target directory: `scope.json`, `scope.txt`, `guidelines.json`, `guidelines.txt`, `README.md`. Never modify the raw file. Delete any scratch file you create; the launcher fails the run on leftover files.
4. Do not invent assets, rules, numbers or quotes.

## Fidelity rules

- Precedence. If the source states which part wins when parts disagree, follow that and record the rule in `notes`. If it states none, an explicit narrower statement beats a general one, and a conflict you cannot settle goes to `review_required`.
- Completeness. Preserve every in-scope and out-of-scope asset and every material program rule. Nothing is dropped silently. Each raw asset token (URL, host, wildcard, IP, CIDR) must appear in `scope.json` in the list where it belongs, or in `review_required`, or, if it is incidental (a documentation link, a platform page), in `non_asset_references` with a reason.
- Recon versus non-recon. `recon_targets` holds only what recon tooling can act on: hostnames, wildcards, URLs, API URLs, IPs, CIDRs. Everything else in scope goes to the optional block `non_recon_in_scope` (keys mobile_apps, store_urls, source_repositories, saas_configuration, content_authorization, other). Asset-less statements go to `other`.
- Ambiguity. First try to resolve it from elsewhere in the same raw file. When another part settles it, apply that and do not flag it. Use `review_required` only when the source stays genuinely ambiguous after reading all of it; give `reason` the specific competing evidence and `source_context` a verbatim nearby quote. An unresolved item is never a recon target.
- Exclusions. An out-of-scope asset is never in `recon_targets`. If a broad wildcard is in scope and a narrower host or path is excluded, keep both and keep the path. Honor tier-specific exclusions.
- Exact values. Preserve URLs with scheme and path. Domains are hostnames only. Wildcards keep their `*` form; if the source gives a mangled wildcard, record the form the source implies and note the original in `notes`. De-duplicate exact repeats inside a list.
- Rules. Capture, per the source: disposition categories, safe-harbor and disclosure terms, tier eligibility and reward ranges, known duplicates, excluded submission types and out-of-scope vulnerability classes, special cases, required headers, rate, automation, denial of service, credential, third-party, social-engineering, support-channel and data-handling restrictions, and researcher conduct. Keep conditions attached to the rule they modify.
- Quotes. `raw_important_quotes` entries and every `source_text` must be verbatim substrings of the raw file (the validator checks). Paraphrase everywhere else.
- Consistency. All five files describe the same facts. Write the JSON first, then derive the text files from it, then the README. If `review_required` is empty no file may say anything is flagged, unresolved or needing review.

## The four program rules (the rules block)

The program rules bind the human and the agent, and the tools enforce them. Capture each from the source into the `rules` block of `scope.json`, with the program's own words in `source_text` (verbatim from the raw file).

- `automation`: `status` is one of allowed, limited, prohibited, unspecified. Use limited when automated tools are allowed with a condition.
- `ai_use`: `status` is one of allowed, disclosure_required, restricted, prohibited, unspecified. Use disclosure_required when AI use must be stated in the report.
- `rate_limit`: either `value` (a number), `unit` (one of per_second, per_minute, per_hour) and `source_text`, or `{"status": "unspecified"}`. A number with no unit is a failure: the unit lives next to the number. Convert nothing; if the source says per minute, write per_minute.
- `identification_header`: either `name`, `value` and `source_text` exactly as the program states, or `{"status": "unspecified"}`.
- `confirmed_by_human`: always `false`. You never set it to true; the human does, with `python3 tools/scope_check.py confirm --target [target]` after reading your quotes.

There is no default header. If the program names none, write `{"status": "unspecified"}` in the rules block, set `required_header` to null, add `required_header` and `rules.identification_header` to `absent_in_source`, and say in your final response that the human must decide. Do not invent a name, a value or a handle, and do not copy one from an example. Every rule that says unspecified is also named in `absent_in_source` as `rules.automation`, `rules.ai_use`, `rules.rate_limit` or `rules.identification_header`.

## Output file schemas (schema_version "1.1")

### scope.json

~~~json
{
  "schema_version": "1.1",
  "target_name": "",
  "platform": "",
  "source_file": "[repo-relative path from Task parameters]",
  "required_header": {"name": "", "value": "", "source_text": ""},
  "recon_targets": {"domains": [], "wildcards": [], "urls": [], "api_urls": [], "ips": [], "cidrs": []},
  "non_recon_in_scope": {"mobile_apps": [], "store_urls": [], "source_repositories": [], "saas_configuration": [], "content_authorization": [], "other": []},
  "out_of_scope": {"domains": [], "wildcards": [], "urls": [], "api_urls": [], "ips": [], "cidrs": [], "mobile_apps": [], "other": []},
  "review_required": [{"value": "", "reason": "", "source_context": ""}],
  "non_asset_references": [{"value": "", "reason": ""}],
  "notes": [],
  "absent_in_source": [],
  "rules": {
    "automation": {"status": "", "source_text": ""},
    "ai_use": {"status": "", "source_text": ""},
    "rate_limit": {"value": 0, "unit": "per_minute", "source_text": ""},
    "identification_header": {"name": "", "value": "", "source_text": ""},
    "confirmed_by_human": false
  }
}
~~~

`required_header` is null when the source requires none. All list members are strings. Every key must be present even when empty. `out_of_scope.other` holds exclusions that are not a single asset.

### scope.txt

~~~text
# Target: [target_name]
# Platform: [platform]
# Source: [source_file]
# Required header: [Name: value, or none]

[in_scope_domains]
[in_scope_wildcards]
[in_scope_urls]
[in_scope_api_urls]
[in_scope_ips]
[in_scope_cidrs]
[non_recon_in_scope]
[out_of_scope]
[review_required]
~~~

One value per line under each section, exactly the strings in the JSON. `[non_recon_in_scope]` lists every non-recon value; `[out_of_scope]` lists every out-of-scope value from all categories; `[review_required]` lines are `value | reason`. Emit all nine sections even when empty.

### guidelines.json

~~~json
{
  "schema_version": "1.1",
  "target_name": "", "platform": "", "source_file": "",
  "authorization": {"only_listed_targets_authorized": false, "safe_harbor_present": false, "safe_harbor": "", "disclosure": "", "notes": []},
  "testing_rules": {
    "required_headers": [],
    "automated_scanning": "", "rate_limits": "", "dos": "", "credentials": "",
    "third_party": "", "support_or_live_chat": "", "social_engineering": "",
    "data_handling": "", "other_restrictions": []
  },
  "disposition_types": [{"name": "", "meaning": ""}],
  "focus_areas": [],
  "out_of_scope_vulnerability_classes": [],
  "known_duplicates": [],
  "reward_tiers": [{"tier": "", "assets": [], "eligibility": "", "severity_ranges": {}, "notes": ""}],
  "reward_or_priority_notes": [],
  "special_cases": [],
  "researcher_conduct": [],
  "submission_notes": [],
  "absent_in_source": [],
  "raw_important_quotes": []
}
~~~

- `testing_rules.required_headers` is the list of `Name: value` strings (empty when none).
- `authorization.safe_harbor` and `disclosure` quote or tightly paraphrase the terms. Set `safe_harbor_present` true only when the source grants it.
- `absent_in_source` names the categories the source does not address, so an empty value is a recorded fact: authorization.safe_harbor, authorization.disclosure, known_duplicates, disposition_types, out_of_scope_vulnerability_classes, reward_tiers, focus_areas, testing_rules.dos, testing_rules.social_engineering, testing_rules.credentials, testing_rules.third_party, testing_rules.support_or_live_chat, testing_rules.automated_scanning_or_rate_limits, researcher_conduct, required_header. Do not use it to avoid work: the validator flags a category the raw text clearly mentions.
- Empty string, empty array or false for anything not mentioned.

### guidelines.txt

Human-readable, rendered from `guidelines.json`. Start with `Target Guidelines - [target_name]` and `Source: [source_file]`, then plain sections (Required Header, Authorization, Disposition Categories, Do Not Test and Restrictions, Credentials, Automation and Rate Limits, Reward Tiers, Focus Areas, Out-of-Scope Classes, Known Duplicates, Special Cases, Researcher Conduct, Important Notes; omit a section only if its JSON source is empty). Write every string from the JSON list fields and rule fields verbatim as its own bullet. The required-header section says `none` when there is none.

### README.md

~~~markdown
# [target_name] Target Scope
What: Generated summary of the organized scope for [target_name].
Who writes: scripts/organize_scope_claude.sh through its agent.
Who reads: You, before running tools/recon.py.
Wired into: [raw filename] (one-way: input), tools/validate_scope.py (one-way: validator)

## Files

- `[raw filename]`: original pasted program scope
- `scope.json`: structured machine-readable recon scope
- `scope.txt`: flat human-readable scope
- `guidelines.json`: structured testing rules
- `guidelines.txt`: human-readable testing rules

## Required header

`[header]` (or: none detected)

## Recon command

python3 tools/recon.py --scope-json [scope_json path from Task parameters] --target-name [target_name] --output recon_output/[target_name] --dry-run

## Validation summary

[paste the block printed by the validator]

## Notes

[short, factual, consistent with the JSON; list every review_required item here with its reason]
~~~

Put the recon command in a fenced bash block in the real README. Keep `--dry-run` in it: the first run only prints what would be touched. Quote paths and names containing spaces.

## Validation (mandatory, deterministic)

Do not assert that you checked your own work. Run the validator from the repo root; it is the authority.

1. After writing the four JSON and text files, run the validator with `--print-readme-summary` (command in Task parameters). On failure it lists every problem; fix the files and rerun. On success it prints the validation-summary block. Paste that block verbatim into the README; never type counts yourself or reuse numbers from an example.
2. Write the README, then run the validator without `--print-readme-summary`. Repeat until it prints `RESULT: PASS`.
3. If you cannot reach PASS, do not edit the validator and do not claim success. Record the item in `review_required` or `non_asset_references` if that is accurate, otherwise stop and report the failing lines.

## Final response

If the validator printed `RESULT: PASS`, respond with only:

~~~text
Created organized target scope files:
- [target_dir]/scope.json
- [target_dir]/scope.txt
- [target_dir]/guidelines.json
- [target_dir]/guidelines.txt
- [target_dir]/README.md

Validator: PASS
- recon targets: [n]   non-recon in-scope: [n]   out-of-scope: [n]   review-required: [n]
- required header: [value or none]
- rules: automation [status], ai use [status], rate limit [value and unit or unspecified], header [name or unspecified]
- unresolved: [none, or each review_required value and reason]

Next: the human reads the quoted rules and runs python3 tools/scope_check.py confirm --target [target]
~~~

Otherwise respond `FAILED` followed by the validator's failing lines. Do not include long explanations.
