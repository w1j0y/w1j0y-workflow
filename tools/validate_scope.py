#!/usr/bin/env python3
# What: Offline validator for the five organized scope files, including the program rules block.
# Who writes: the repo author (sanitized from an earlier private validator).
# Who reads: scripts/lib/organize_scope_common.sh runs it; the human runs it after editing a scope file.
# Wired into: scripts/lib/organize_scope_common.sh, tools/recon.py (--validate-scope-only), prompts/organize_scope.md
"""Offline validator for organized bug bounty scope files. No LLM, no network.

Why this is a tool and not a paragraph in the organizer prompt: the prompt used to
ask the model to "validate locally", which let a run print a success summary whose
counts were copied from a template and whose text files had drifted from the JSON.
This script is what `scripts/organize_scope_claude.sh` runs after the agent finishes; a
non-zero exit means the organization did NOT complete.

Checks (all deterministic):
  1. scope.json / guidelines.json parse and carry the required schema keys.
  2. Every asset token found in the raw file (URL, hostname, wildcard, IPv4, CIDR)
     appears in the generated JSON, or is recorded in scope.json
     `non_asset_references` with a reason, or sits in `review_required`.
  3. Every bullet/list line in the raw file is fuzzily represented in the JSON.
  4. Keyword-triggered policy categories (safe harbor, disclosure, duplicates,
     excluded submission types, rewards, DoS, credentials, ...) are non-empty in
     guidelines.json, or named in `absent_in_source`.
  5. No out-of-scope asset is a recon target (exact, wildcard, host, path, CIDR).
  6. scope.txt, guidelines.txt and README.md agree with the JSON; the README
     validation summary carries the counts computed here; no stale review notes.
  7. raw_important_quotes and every rules source_text occur verbatim in the raw.
  8. The rules block: automation, ai_use, rate_limit, identification_header and
     confirmed_by_human. A rule that says unspecified must be listed in
     scope.json absent_in_source; the rate limit carries a unit next to the value.

Coverage limit: asset POLARITY (in vs out of scope) cannot be derived from raw text
deterministically, so check 2 proves an asset is represented, not that it sits in the
right list. Check 5 catches the dangerous direction only where the JSON itself
records the exclusion.

Exit codes: 0 pass, 1 validation failure, 2 usage error.
"""

import argparse
import ipaddress
import json
import os
import re
import shlex
import sys
from pathlib import Path

SCHEMA_VERSION = "1.1"
RULE_NAMES = ["automation", "ai_use", "rate_limit", "identification_header"]
AUTOMATION_STATUS = {"allowed", "limited", "prohibited", "unspecified"}
AI_USE_STATUS = {"allowed", "disclosure_required", "restricted", "prohibited", "unspecified"}
RATE_UNITS = {"per_second", "per_minute", "per_hour"}

RECON_KEYS = ["domains", "wildcards", "urls", "api_urls", "ips", "cidrs"]
NON_RECON_KEYS = ["mobile_apps", "store_urls", "source_repositories", "saas_configuration",
                  "content_authorization", "other"]
OOS_KEYS = ["domains", "wildcards", "urls", "api_urls", "ips", "cidrs", "mobile_apps", "other"]
SCOPE_TOP = ["schema_version", "target_name", "platform", "source_file",
             "required_header", "recon_targets",
             "out_of_scope", "review_required", "non_asset_references", "notes",
             "absent_in_source", "rules"]
GUIDE_TOP = ["schema_version", "target_name", "platform", "source_file",
             "authorization", "testing_rules", "disposition_types", "focus_areas",
             "out_of_scope_vulnerability_classes", "known_duplicates", "reward_tiers",
             "reward_or_priority_notes", "special_cases", "researcher_conduct",
             "submission_notes", "absent_in_source", "raw_important_quotes"]
AUTH_KEYS = ["only_listed_targets_authorized", "safe_harbor_present", "safe_harbor",
             "disclosure", "notes"]
TEST_RULE_STR = ["automated_scanning", "rate_limits", "dos", "credentials", "third_party",
            "support_or_live_chat", "social_engineering", "data_handling"]
RULE_LIST = ["required_headers", "other_restrictions"]
GUIDE_STR_LISTS = ["focus_areas", "out_of_scope_vulnerability_classes", "known_duplicates",
                   "reward_or_priority_notes", "special_cases", "researcher_conduct",
                   "submission_notes", "raw_important_quotes"]

IGNORE_DOMAINS = ("hackerone.com", "bugcrowd.com", "intigriti.com", "yeswehack.com",
                  "hackenproof.com", "immunefi.com", "synack.com", "first.org", "nist.gov",
                  "mitre.org", "owasp.org", "w3.org")
FALSE_HOSTS = {"asp.net", "node.js", "next.js", "vue.js", "react.js", "e.g", "i.e"}
BAD_TLDS = {"json", "txt", "html", "htm", "png", "jpg", "jpeg", "gif", "svg", "pdf", "md", "js",
            "py", "sh", "rb", "go", "rs", "ts", "css", "yaml", "yml", "xml", "csv", "log",
            "zip", "gz", "tar", "exe", "dll", "php", "asp", "aspx", "jsp", "do", "action",
            "portal", "conf", "cfg", "ini", "bak", "sql", "so", "lock", "toml"}

URL_RE = re.compile(r"https?://[^\s<>\"'`\]}]+", re.I)
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
IPV4_RE = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?:/(\d{1,2}))?(?![\w]|\.\d)")
HOST_RE = re.compile(r"(?<![\w@./-])((?:\*\.)?(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,24})(?![\w-])", re.I)
BARE_PATTERN_RE = re.compile(r"^(?:https?://)?((?:\*\.)?(?:[a-z0-9-]+\.)+[a-z]{2,24})(/\S*)?$", re.I)
BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.+?)\s*$")
STOP = set("this that with from have will your their they them than then also when which what "
           "where while into onto over only must should would could about other such these "
           "those been being were does done each more most some very just like".split())

# keyword in raw -> (label, getter over guidelines dict). Satisfied when non-empty or the
# label is named in guidelines.absent_in_source.
KEYWORD_CHECKS = [
    (r"safe[- ]harbou?r", "authorization.safe_harbor",
     lambda g: g["authorization"].get("safe_harbor_present") is True
     and bool(str(g["authorization"].get("safe_harbor", "")).strip())),
    (r"disclos", "authorization.disclosure",
     lambda g: bool(str(g["authorization"].get("disclosure", "")).strip())),
    (r"known (?:issues|duplicates)|duplicate if|already (?:known|reported)|known to us",
     "known_duplicates", lambda g: bool(g.get("known_duplicates"))),
    (r"\b(?:informative|non[- ]rewardable|not applicable)\b", "disposition_types",
     lambda g: bool(g.get("disposition_types"))),
    (r"excluded submission|out[- ]of[- ]scope (?:findings|submissions?|vulnerabilit)|"
     r"ineligible|not eligible|non[- ]qualifying", "out_of_scope_vulnerability_classes",
     lambda g: bool(g.get("out_of_scope_vulnerability_classes"))),
    (r"\$\s?\d", "reward_tiers", lambda g: bool(g.get("reward_tiers"))),
    (r"focus area|priority areas?|in[- ]focus", "focus_areas", lambda g: bool(g.get("focus_areas"))),
    (r"\b(?:dos|ddos|denial[- ]of[- ]service)\b", "testing_rules.dos",
     lambda g: bool(g["testing_rules"].get("dos", "").strip())),
    (r"social engineering|phishing", "testing_rules.social_engineering",
     lambda g: bool(g["testing_rules"].get("social_engineering", "").strip())),
    (r"credential", "testing_rules.credentials",
     lambda g: bool(g["testing_rules"].get("credentials", "").strip())),
    (r"third[- ]part(?:y|ies)", "testing_rules.third_party",
     lambda g: bool(g["testing_rules"].get("third_party", "").strip())),
    (r"live chat|support agent", "testing_rules.support_or_live_chat",
     lambda g: bool(g["testing_rules"].get("support_or_live_chat", "").strip())),
    (r"automated|scanner|scanning|rate[- ]limit", "testing_rules.automated_scanning_or_rate_limits",
     lambda g: bool(g["testing_rules"].get("automated_scanning", "").strip()
                    or g["testing_rules"].get("rate_limits", "").strip())),
    (r"good[- ]faith|privacy violation|do not (?:access|disclose|exfiltrate|modify|destroy)|must not",
     "researcher_conduct", lambda g: bool(g.get("researcher_conduct"))),
]
STALE_RE = re.compile(r"flagged for review|needs? (?:manual )?review|pending review|unresolved", re.I)


def fold(text):
    """Whitespace/typography-insensitive form used for verbatim comparisons."""
    text = (text.replace("’", "'").replace("‘", "'").replace("“", '"')
            .replace("”", '"').replace("\u2013", "-").replace("\u2014", "-")
            .replace(" ", " "))
    return re.sub(r"\s+", " ", text).strip().lower()


def walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, list):
        for item in node:
            yield from walk_strings(item)
    elif isinstance(node, dict):
        for value in node.values():
            yield from walk_strings(value)


def header_str(scope):
    """'Name: value' for the scope's required header, or '' when there is none."""
    h = scope.get("required_header")
    if isinstance(h, dict) and h.get("name") and h.get("value"):
        return f"{h['name']}: {h['value']}"
    return ""


def nonrecon_of(scope):
    """The optional non_recon_in_scope block, with every key present."""
    block = scope.get("non_recon_in_scope")
    block = block if isinstance(block, dict) else {}
    return {k: block.get(k, []) for k in NON_RECON_KEYS}


def as_str_list(value):
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, check, msg):
        self.errors.append((check, msg))

    def warn(self, check, msg):
        self.warnings.append((check, msg))


def load_json(path, report, check):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        report.err(check, f"missing file: {path}")
        return None
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        report.err(check, f"{path} does not parse as JSON: {exc}")
        return None
    if not isinstance(data, dict):
        report.err(check, f"{path} root must be an object")
        return None
    return data


def check_lists(obj, keys, where, report, check="schema"):
    if not isinstance(obj, dict):
        report.err(check, f"{where} must be an object")
        return
    for key in keys:
        if key not in obj:
            report.err(check, f"{where}.{key} missing")
        elif not isinstance(obj[key], list) or not all(isinstance(v, str) for v in obj[key]):
            report.err(check, f"{where}.{key} must be a list of strings")
        elif len(set(obj[key])) != len(obj[key]):
            report.err(check, f"{where}.{key} contains exact duplicates")


def check_schema(scope, guide, report):
    for name, data, top in (("scope.json", scope, SCOPE_TOP), ("guidelines.json", guide, GUIDE_TOP)):
        for key in top:
            if key not in data:
                report.err("schema", f"{name} missing top-level key: {key}")
        if data.get("schema_version") != SCHEMA_VERSION:
            report.err("schema", f'{name} schema_version must be "{SCHEMA_VERSION}"')
        for key in ("target_name", "platform", "source_file"):
            if not isinstance(data.get(key), str) or not data.get(key, "").strip():
                report.err("schema", f"{name} {key} must be a non-empty string")
    for key in ("target_name", "platform", "source_file"):
        if scope.get(key) != guide.get(key):
            report.err("consistency", f"scope.json and guidelines.json disagree on {key}")

    rh = scope.get("required_header")
    if rh is not None and not (isinstance(rh, dict) and all(
            isinstance(rh.get(k), str) and rh.get(k).strip() for k in ("name", "value"))):
        report.err("schema", "scope.json required_header must be null or an object with name and value")
    check_lists(scope.get("recon_targets"), RECON_KEYS, "scope.recon_targets", report)
    if "non_recon_in_scope" in scope:
        check_lists(scope.get("non_recon_in_scope"), NON_RECON_KEYS, "scope.non_recon_in_scope", report)
    check_lists(scope.get("out_of_scope"), OOS_KEYS, "scope.out_of_scope", report)
    check_lists(scope, ["notes", "absent_in_source"], "scope", report)
    for key in ("review_required", "non_asset_references"):
        if not isinstance(scope.get(key), list):
            report.err("schema", f"scope.{key} must be a list")
    for key, fields in (("review_required", ("value", "reason", "source_context")),
                        ("non_asset_references", ("value", "reason"))):
        for i, e in enumerate(scope.get(key) or []):
            if not (isinstance(e, dict) and all(isinstance(e.get(k), str) and e.get(k).strip()
                                                for k in fields)):
                report.err("schema", f"scope.{key}[{i}] needs non-empty {', '.join(fields)}")

    auth, rules = guide.get("authorization"), guide.get("testing_rules")
    if not isinstance(auth, dict):
        report.err("schema", "guidelines.authorization must be an object")
    else:
        for key in AUTH_KEYS:
            if key not in auth:
                report.err("schema", f"guidelines.authorization.{key} missing")
        for key in ("only_listed_targets_authorized", "safe_harbor_present"):
            if not isinstance(auth.get(key), bool):
                report.err("schema", f"guidelines.authorization.{key} must be boolean")
        for key in ("safe_harbor", "disclosure"):
            if not isinstance(auth.get(key), str):
                report.err("schema", f"guidelines.authorization.{key} must be a string")
        check_lists(auth, ["notes"], "guidelines.authorization", report)
    if not isinstance(rules, dict):
        report.err("schema", "guidelines.testing_rules must be an object")
    else:
        for key in TEST_RULE_STR:
            if not isinstance(rules.get(key), str):
                report.err("schema", f"guidelines.testing_rules.{key} must be a string")
        check_lists(rules, RULE_LIST, "guidelines.testing_rules", report)
    check_lists(guide, GUIDE_STR_LISTS + ["absent_in_source"], "guidelines", report)
    for key, field in (("disposition_types", "name"), ("reward_tiers", "tier")):
        entries = guide.get(key)
        if not isinstance(entries, list) or not all(
                isinstance(e, dict) and isinstance(e.get(field), str) and e[field].strip()
                for e in entries):
            report.err("schema", f"guidelines.{key} must be a list of objects with a non-empty '{field}'")


# ---------------------------------------------------------------- raw asset extraction

def valid_ip(text):
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


def trim_url(url):
    url = url.rstrip(".,;:!?'\"")
    while url.endswith(")") and url.count(")") > url.count("("):
        url = url[:-1].rstrip(".,;:!?'\"")
    return url


def ignored_host(host):
    host = host.lower().lstrip("*.")
    return host in FALSE_HOSTS or any(host == d or host.endswith("." + d) for d in IGNORE_DOMAINS)


def extract_assets(raw):
    """Return the set of asset tokens a human would call a target in the raw text."""
    tokens, text = set(), raw
    for m in URL_RE.finditer(raw):
        url = trim_url(m.group(0))
        host = re.sub(r"^https?://", "", url, flags=re.I).split("/")[0].split(":")[0]
        if not ignored_host(host):
            tokens.add(url)
    text = URL_RE.sub(" ", text)
    text = EMAIL_RE.sub(" ", text)
    for m in IPV4_RE.finditer(text):
        ip, prefix = m.group(1), m.group(2)
        if not valid_ip(ip):
            continue
        if prefix is not None:
            if int(prefix) <= 32:
                tokens.add(f"{ip}/{prefix}")
        else:
            tokens.add(ip)
    text = IPV4_RE.sub(" ", text)
    for m in HOST_RE.finditer(text):
        host = m.group(1)
        tld = host.rsplit(".", 1)[1].lower()
        if tld in BAD_TLDS or ignored_host(host):
            continue
        tokens.add(host)
    unique = {}
    for t in sorted(tokens):
        unique.setdefault(fold(t), t)
    return set(unique.values())


def token_present(token, blob_fold):
    t = fold(token)
    if t in blob_fold:
        return True
    stripped = re.sub(r"^https?://", "", t).rstrip("/")
    return bool(stripped) and stripped in blob_fold


def list_items(raw):
    items = []
    for line in raw.splitlines():
        m = BULLET_RE.match(line)
        if m and len(m.group(1)) >= 8:
            items.append(m.group(1))
    return items


def content_words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if len(w) >= 4 and w not in STOP}


# ---------------------------------------------------------------- scope polarity checks

def host_matches(host, pattern):
    host, pattern = host.lower().rstrip("."), pattern.lower()
    if pattern.startswith("*."):
        return host.endswith(pattern[1:]) and host != pattern[2:]
    return host == pattern


def split_url(value):
    m = BARE_PATTERN_RE.match(value.strip())
    if not m:
        return None
    host, path = m.group(1).lower(), (m.group(2) or "")
    path = path.rstrip("*").rstrip("/")
    return host, path


def oos_patterns(oos):
    """(host_pattern, path_prefix) for every out-of-scope entry shaped like an asset."""
    out = []
    for key in ("domains", "wildcards", "urls", "api_urls", "other"):
        for value in as_str_list(oos.get(key)):
            parsed = split_url(value)
            if parsed:
                out.append(parsed)
    return out


def check_conflicts(scope, report):
    recon, oos, nonrecon = scope["recon_targets"], scope["out_of_scope"], nonrecon_of(scope)
    oos_all = {fold(v).rstrip("/") for k in OOS_KEYS for v in as_str_list(oos.get(k))}
    for key in RECON_KEYS:
        for v in as_str_list(recon.get(key)):
            if fold(v).rstrip("/") in oos_all:
                report.err("oos-in-recon", f"recon_targets.{key} contains out-of-scope value: {v}")
    for key in NON_RECON_KEYS:
        for v in as_str_list(nonrecon.get(key)):
            if fold(v).rstrip("/") in oos_all:
                report.err("oos-in-recon", f"non_recon_in_scope.{key} contains out-of-scope value: {v}")
    review = {fold(str(e.get("value", ""))).rstrip("/") for e in scope["review_required"]
              if isinstance(e, dict)}
    for key in RECON_KEYS:
        for v in as_str_list(recon.get(key)):
            if fold(v).rstrip("/") in review:
                report.err("oos-in-recon", f"review_required value is also a recon target: {v}")

    patterns = oos_patterns(oos)
    for key in ("domains", "urls", "api_urls"):
        for v in as_str_list(recon.get(key)):
            parsed = split_url(v)
            if not parsed:
                continue
            host, path = parsed
            for ohost, opath in patterns:
                if not host_matches(host, ohost):
                    continue
                if not opath or (path and path.startswith(opath)):
                    report.err("oos-in-recon", f"recon_targets.{key} entry {v} is covered by "
                                              f"out-of-scope pattern {ohost}{opath}")
                    break
    for v in as_str_list(recon.get("wildcards")):
        w = v.lower()
        for ohost, opath in patterns:
            if not opath and ohost.startswith("*.") and w.endswith(ohost[1:]):
                report.err("oos-in-recon", f"recon wildcard {v} is covered by out-of-scope wildcard {ohost}")
    oos_nets = []
    for key in ("ips", "cidrs"):
        for v in as_str_list(oos.get(key)):
            try:
                oos_nets.append(ipaddress.ip_network(v.strip(), strict=False))
            except ValueError:
                report.err("schema", f"out_of_scope.{key} is not a valid IP/CIDR: {v}")
    for key in ("ips", "cidrs"):
        for v in as_str_list(recon.get(key)):
            try:
                net = ipaddress.ip_network(v.strip(), strict=False)
            except ValueError:
                report.err("schema", f"recon_targets.{key} is not a valid IP/CIDR: {v}")
                continue
            if any(net.version == o.version and net.overlaps(o) for o in oos_nets):
                report.err("oos-in-recon", f"recon_targets.{key} entry {v} overlaps out-of-scope IP space")
    for key in ("domains",):
        for v in as_str_list(recon.get(key)):
            if "://" in v or "/" in v or "*" in v:
                report.err("schema", f"recon_targets.{key} must be hostnames only: {v}")
    for v in as_str_list(recon.get("wildcards")):
        if "*" not in v:
            report.err("schema", f"recon_targets.wildcards entry has no '*': {v}")
    for key in ("urls", "api_urls"):
        for v in as_str_list(recon.get(key)):
            if not re.match(r"^https?://", v):
                report.err("schema", f"recon_targets.{key} entry needs a scheme: {v}")


# ---------------------------------------------------------------- program rules block

def check_rules(scope, raw, report):
    """The rules block: shape, verbatim quotes, unspecified listed as absent, unit next to value."""
    rules = scope.get("rules")
    if not isinstance(rules, dict):
        report.err("rules", "scope.json rules must be an object")
        return
    rawf = fold(raw)
    absent = set(as_str_list(scope.get("absent_in_source")))
    for name in RULE_NAMES:
        if name not in rules:
            report.err("rules", f"rules.{name} missing")
    if not isinstance(rules.get("confirmed_by_human"), bool):
        report.err("rules", "rules.confirmed_by_human must be boolean")

    def quote_ok(name, text):
        if not isinstance(text, str) or not text.strip():
            report.err("rules", f"rules.{name}.source_text must be a non-empty string")
        elif fold(text) not in rawf:
            report.err("rules", f"rules.{name}.source_text is not verbatim in the raw file: {text[:120]}")

    def unspecified(name):
        if f"rules.{name}" not in absent and name not in absent:
            report.err("rules", f"rules.{name} is unspecified but 'rules.{name}' is not listed "
                                f"in absent_in_source")

    for name, allowed in (("automation", AUTOMATION_STATUS), ("ai_use", AI_USE_STATUS)):
        rule = rules.get(name)
        if not isinstance(rule, dict):
            continue
        status = rule.get("status")
        if status not in allowed:
            report.err("rules", f"rules.{name}.status must be one of {sorted(allowed)}, got {status!r}")
        elif status == "unspecified":
            unspecified(name)
        else:
            quote_ok(name, rule.get("source_text"))

    rate = rules.get("rate_limit")
    if isinstance(rate, dict):
        if rate.get("status") == "unspecified" and "value" not in rate:
            unspecified("rate_limit")
        else:
            value = rate.get("value")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                report.err("rules", f"rules.rate_limit.value must be a positive number, got {value!r}")
            if rate.get("unit") not in RATE_UNITS:
                report.err("rules", f"rules.rate_limit.unit must be one of {sorted(RATE_UNITS)}; "
                                    f"a number with no unit is not a rate")
            quote_ok("rate_limit", rate.get("source_text"))

    ident = rules.get("identification_header")
    header = scope.get("required_header")
    if isinstance(ident, dict):
        if ident.get("status") == "unspecified" and "name" not in ident:
            unspecified("identification_header")
            if header:
                report.err("rules", "required_header is set but rules.identification_header is unspecified")
        else:
            for k in ("name", "value"):
                if not isinstance(ident.get(k), str) or not ident.get(k).strip():
                    report.err("rules", f"rules.identification_header.{k} must be a non-empty string")
            quote_ok("identification_header", ident.get("source_text"))
            if not isinstance(header, dict):
                report.err("rules", "rules.identification_header is set but required_header is null")
            elif (header.get("name"), header.get("value")) != (ident.get("name"), ident.get("value")):
                report.err("rules", "rules.identification_header disagrees with required_header")


# ---------------------------------------------------------------- raw coverage

def check_raw_coverage(raw, scope, guide, report):
    blob = list(walk_strings(scope)) + list(walk_strings(guide))
    blob_fold = fold("\n".join(blob))
    blob_words = {w for s in blob for w in re.findall(r"[a-z0-9]+", s.lower())}
    assets = extract_assets(raw)
    missing = sorted(t for t in assets if not token_present(t, blob_fold))
    for t in missing:
        report.err("raw-coverage", f"raw asset not represented in generated JSON "
                                   f"(add it to its scope list, review_required, or "
                                   f"non_asset_references with a reason): {t}")
    items = list_items(raw)
    checked = 0
    for item in items:
        if extract_assets(item):
            continue
        words = content_words(item)
        if not words:
            continue
        checked += 1
        hit = len(words & blob_words)
        if hit * 2 < len(words) or (len(words) <= 2 and hit < len(words)):
            report.err("raw-coverage", f"raw list item not represented in generated JSON: {item[:140]}")

    rawf = fold(raw)
    absent = set(as_str_list(guide.get("absent_in_source"))) | set(as_str_list(scope.get("absent_in_source")))
    for pattern, label, getter in KEYWORD_CHECKS:
        if re.search(pattern, raw, re.I) and not getter(guide) and label not in absent:
            report.err("policy-coverage", f"raw mentions /{pattern}/ but guidelines.json has nothing "
                                          f"for '{label}' (fill it, or list it in absent_in_source)")
    for label in absent:
        known = {lab for _, lab, _ in KEYWORD_CHECKS} | set(GUIDE_TOP) | {"required_header"} | {f"rules.{n}" for n in RULE_NAMES}
        if label not in known:
            report.warn("policy-coverage", f"absent_in_source names unknown category: {label}")
    if (re.search(r"(?:add|include|use|set|send|require[sd]?|provide|attach|pass)[^.\n]{0,80}\bheaders?\b", raw, re.I)
            and not scope.get("required_header") and "required_header" not in absent
            and "rules.identification_header" not in absent):
        report.err("policy-coverage", "raw mentions adding/using a header but scope.json "
                                      "required_header is empty (record it, or list "
                                      "'required_header' in absent_in_source)")
    for quote in as_str_list(guide.get("raw_important_quotes")):
        if fold(quote) not in rawf:
            report.err("quotes", f"raw_important_quotes entry is not verbatim in the raw file: {quote[:120]}")
    return len(assets), checked, len(scope.get("non_asset_references") or [])


# ---------------------------------------------------------------- text-file consistency

def counts(scope):
    recon = sum(len(as_str_list(scope["recon_targets"].get(k))) for k in RECON_KEYS)
    nonrecon = sum(len(as_str_list(nonrecon_of(scope).get(k))) for k in NON_RECON_KEYS)
    oos = sum(len(as_str_list(scope["out_of_scope"].get(k))) for k in OOS_KEYS)
    return recon, nonrecon, oos, len(scope["review_required"])


def parse_scope_txt(text):
    header, sections, current = {}, {}, None
    for line in text.splitlines():
        s = line.strip()
        m = re.match(r"^#\s*(Target|Platform|Source|Required header):\s*(.*)$", s)
        if m:
            header[m.group(1)] = m.group(2).strip()
        elif re.match(r"^\[[a-z_]+\]$", s):
            current = s[1:-1]
            sections.setdefault(current, [])
        elif s and not s.startswith("#") and current:
            sections[current].append(s)
    return header, sections


def check_scope_txt(path, scope, report):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        report.err("scope.txt", f"cannot read {path}: {exc}")
        return ""
    header, sections = parse_scope_txt(text)
    want_header = header_str(scope) or "none"
    for key, want in (("Target", scope["target_name"]), ("Platform", scope["platform"]),
                      ("Source", scope["source_file"]), ("Required header", want_header)):
        if header.get(key) != want:
            report.err("scope.txt", f"header '# {key}:' is {header.get(key)!r}, JSON says {want!r}")
    expected = {f"in_scope_{k}": as_str_list(scope["recon_targets"][k]) for k in RECON_KEYS}
    expected["non_recon_in_scope"] = [v for k in NON_RECON_KEYS for v in nonrecon_of(scope)[k]]
    expected["out_of_scope"] = [v for k in OOS_KEYS for v in scope["out_of_scope"][k]]
    expected["review_required"] = [f"{e['value']} | {e['reason']}" for e in scope["review_required"]
                                   if isinstance(e, dict)]
    for name, want in expected.items():
        if name not in sections:
            report.err("scope.txt", f"missing section [{name}]")
            continue
        got, want_n = sorted(sections[name]), sorted(want)
        if got != want_n:
            extra = sorted(set(got) - set(want_n))[:3]
            lost = sorted(set(want_n) - set(got))[:3]
            report.err("scope.txt", f"[{name}] disagrees with scope.json "
                                    f"({len(got)} lines vs {len(want_n)} entries; "
                                    f"only in txt: {extra}; only in json: {lost})")
    for name in sections:
        if name not in expected:
            report.err("scope.txt", f"unexpected section [{name}]")
    return text


def check_guidelines_txt(path, scope, guide, report):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        report.err("guidelines.txt", f"cannot read {path}: {exc}")
        return ""
    tf = fold(text)
    wants = [guide["target_name"], guide["source_file"]]
    wants += [header_str(scope)] if header_str(scope) else []
    auth, rules = guide["authorization"], guide["testing_rules"]
    wants += [auth.get("safe_harbor", ""), auth.get("disclosure", "")] + as_str_list(auth.get("notes"))
    wants += [rules.get(k, "") for k in TEST_RULE_STR] + as_str_list(rules.get("other_restrictions"))
    for key in GUIDE_STR_LISTS:
        if key != "raw_important_quotes":
            wants += as_str_list(guide.get(key))
    wants += [e["name"] for e in guide["disposition_types"] if isinstance(e, dict)]
    wants += [e["tier"] for e in guide["reward_tiers"] if isinstance(e, dict)]
    for want in wants:
        if isinstance(want, str) and want.strip() and fold(want) not in tf:
            report.err("guidelines.txt", f"not in guidelines.txt (must agree with guidelines.json): {want[:120]}")
    if not header_str(scope) and "none" not in tf.split("required header", 1)[-1][:80]:
        report.warn("guidelines.txt", "no required header recorded; section should say 'none'")
    return text


def check_readme(path, scope, tallies, report):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        report.err("README.md", f"cannot read {path}: {exc}")
        return ""
    if not text.startswith(f"# {scope['target_name']} Target Scope"):
        report.err("README.md", f"first line must be '# {scope['target_name']} Target Scope'")
    for f in ("scope.json", "scope.txt", "guidelines.json", "guidelines.txt"):
        if f"`{f}`" not in text:
            report.err("README.md", f"Files section does not list `{f}`")
    if os.path.basename(scope["source_file"]) not in text:
        report.err("README.md", "Files section does not name the raw source file")
    header = header_str(scope)
    rel_scope = scope["_scope_json_rel"]
    cmd = [l for l in text.splitlines() if "--scope-json" in l or "--header" in l]
    joined = " ".join(cmd)
    if rel_scope not in joined and shlex.quote(rel_scope) not in joined:
        report.err("README.md", f"recon command does not use --scope-json {rel_scope}")
    if "--target-name" not in text:
        report.err("README.md", "recon command is missing --target-name")
    if "tools/recon.py" not in text:
        report.err("README.md", "recon command does not name tools/recon.py")
    if header:
        if header not in text:
            report.err("README.md", f"README does not state the required header: {header}")
    recon, nonrecon, oos, review = tallies["counts"]
    want = {
        "JSON parsed successfully": "yes",
        "Recon targets found": str(recon),
        "Non-recon in-scope entries": str(nonrecon),
        "Out-of-scope entries found": str(oos),
        "Review-required entries": str(review),
        "Required header detected": "yes" if header else "no",
        "Raw-source coverage": coverage_line(tallies),
        "Unresolved items": "none" if not review else f"{review} (see review_required)",
    }
    for label, value in want.items():
        m = re.search(rf"^- {re.escape(label)}: (.*)$", text, re.M)
        if not m:
            report.err("README.md", f"validation summary is missing '- {label}: ...'")
        elif m.group(1).strip() != value:
            report.err("README.md", f"validation summary '{label}' is {m.group(1).strip()!r}; "
                                    f"computed from the JSON: {value!r}")
    for e in scope["review_required"]:
        if isinstance(e, dict) and e.get("value") and e["value"] not in text:
            report.err("README.md", f"unresolved review_required item not listed in README: {e['value'][:100]}")
    return text


def coverage_line(tallies):
    a, l, n = tallies["coverage"]
    return (f"{a} asset tokens and {l} list items checked against the generated JSON; "
            f"{n} recorded as non-asset references")


def check_stale(scope, texts, report):
    if scope["review_required"]:
        return
    pools = [("scope.json notes", "\n".join(as_str_list(scope.get("notes"))))] + list(texts.items())
    for name, text in pools:
        cleaned = re.sub(r"^- (Unresolved items|Review-required entries): .*$", "", text, flags=re.M)
        m = STALE_RE.search(cleaned)
        if m:
            report.err("stale-notes", f"{name} mentions '{m.group(0)}' but review_required is empty")


def summary_block(tallies, header):
    recon, nonrecon, oos, review = tallies["counts"]
    return "\n".join([
        "- JSON parsed successfully: yes",
        f"- Recon targets found: {recon}",
        f"- Non-recon in-scope entries: {nonrecon}",
        f"- Out-of-scope entries found: {oos}",
        f"- Review-required entries: {review}",
        f"- Required header detected: {'yes' if header else 'no'}",
        f"- Raw-source coverage: {coverage_line(tallies)}",
        f"- Unresolved items: {'none' if not review else f'{review} (see review_required)'}",
    ])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--raw-scope", required=True, help="path to the raw scope file")
    ap.add_argument("--target-dir", help="defaults to the raw file's directory")
    ap.add_argument("--repo-root", help="defaults to the parent of tools/")
    ap.add_argument("--require-fresh-since-ns", type=int,
                    help="fail if an output file's mtime is older than this (ns since epoch)")
    ap.add_argument("--print-readme-summary", action="store_true",
                    help="skip README checks and print the validation-summary block computed "
                         "from the generated JSON")
    args = ap.parse_args(argv)

    raw_path = Path(args.raw_scope).resolve()
    target_dir = Path(args.target_dir).resolve() if args.target_dir else raw_path.parent
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[1]
    report = Report()
    try:
        raw = raw_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        print(f"usage error: cannot read raw scope {raw_path}: {exc}", file=sys.stderr)
        return 2

    names = ["scope.json", "scope.txt", "guidelines.json", "guidelines.txt", "README.md"]
    for n in names:
        if args.print_readme_summary and n == "README.md":
            continue  # the summary is printed precisely so the README can be written
        p = target_dir / n
        if not p.is_file():
            report.err("files", f"missing output file: {p}")
        elif p.stat().st_size == 0:
            report.err("files", f"empty output file: {p}")
        elif args.require_fresh_since_ns is not None and p.stat().st_mtime_ns < args.require_fresh_since_ns:
            report.err("files", f"{n} was not written by this run (stale mtime)")

    scope = load_json(target_dir / "scope.json", report, "schema")
    guide = load_json(target_dir / "guidelines.json", report, "schema")
    tallies, texts = None, {}
    if scope is not None and guide is not None:
        before = len(report.errors)
        check_schema(scope, guide, report)
        if len(report.errors) == before:
            try:
                src = Path(scope["source_file"])
                src = src if src.is_absolute() else repo_root / src
                if src.resolve() != raw_path:
                    report.err("consistency", f"source_file {scope['source_file']} does not resolve to {raw_path}")
            except OSError as exc:
                report.err("consistency", f"cannot resolve source_file: {exc}")
            header = header_str(scope)
            listed = guide["testing_rules"].get("required_headers")
            if listed is not None and set(listed) != ({header} if header else set()):
                report.err("consistency", "guidelines.testing_rules.required_headers disagrees with scope.json")
            check_rules(scope, raw, report)
            check_conflicts(scope, report)
            a, l, n = check_raw_coverage(raw, scope, guide, report)
            tallies = {"counts": counts(scope), "coverage": (a, l, n)}
            scope["_scope_json_rel"] = os.path.relpath(target_dir / "scope.json", repo_root)
            texts["scope.txt"] = check_scope_txt(target_dir / "scope.txt", scope, report)
            texts["guidelines.txt"] = check_guidelines_txt(target_dir / "guidelines.txt", scope, guide, report)
            if args.print_readme_summary:
                if not report.errors:
                    print(summary_block(tallies, header))
            else:
                texts["README.md"] = check_readme(target_dir / "README.md", scope, tallies, report)
                check_stale(scope, texts, report)

    for check, msg in report.warnings:
        print(f"WARN [{check}] {msg}", file=sys.stderr)
    if report.errors:
        for check, msg in report.errors:
            print(f"FAIL [{check}] {msg}", file=sys.stderr)
        print(f"RESULT: FAIL ({len(report.errors)} problem(s)) -- scope organization is NOT complete",
              file=sys.stderr)
        return 1
    if not args.print_readme_summary:
        recon, nonrecon, oos, review = tallies["counts"]
        print(f"RESULT: PASS recon_targets={recon} non_recon_in_scope={nonrecon} "
              f"out_of_scope={oos} review_required={review}")
        for e in scope["review_required"]:
            print(f"UNRESOLVED: {e['value']} -- {e['reason']}")
        for label in as_str_list(guide.get("absent_in_source")):
            print(f"ASSERTED-ABSENT-IN-SOURCE: {label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
