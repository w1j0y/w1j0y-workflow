#!/usr/bin/env python3
# What: Scope-bound passive recon (subdomains, probe, archive URLs) that refuses without a header and a rate and filters every host against the scope file.
# Who writes: the repo author; regenerate with tools/_GENERATE_RECON.md.
# Who reads: the human runs it; phase prompts read its output folder under recon_output/[target]/[timestamp]/.
# Wired into: tools/scope_check.py, tools/_TEMPLATE_RECON.md, tools/install_tools.sh, tools/validate_scope.py (one-way: the validator is run by the organizer, not by recon)
"""Scope-bound recon.

Modes:
  --validate-scope-only   check the scope file and print the in-scope seeds; no tool runs.
  --dry-run               print the seeds, rate, header and the exact commands; send nothing.
  --fixture DIR           offline: read saved tool outputs from DIR, apply the same filters,
                          write the run folder. No process is started, no request is made.
  (neither)               live: run subfinder, httpx and gau with the header and rate.

The scope filter runs at three points: after enumeration, after resolution, after probing.
Exit codes: 0 ok, 1 scope file invalid, 2 usage or missing input, 3 refusal.
"""

import argparse
import datetime
import ipaddress
import json
import math
import os
import shlex
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
try:
    from tools.scope_check import host_in_scope  # noqa: E402
except ImportError as exc:  # pragma: no cover - depends on the other tool being present
    print(f"usage error: cannot import tools/scope_check.py ({exc})", file=sys.stderr)
    sys.exit(2)

UNIT_TO_PER_MINUTE = {"per_second": 60.0, "per_minute": 1.0, "per_hour": 1.0 / 60.0}
LOCAL_HOSTS = ("localhost", "127.0.0.1", "::1")
GAU_THREADS = 5
TOOL_TIMEOUT = 1800


class Refusal(Exception):
    """A rule stops the run (exit 3)."""


class Usage(Exception):
    """Bad arguments or a missing input (exit 2)."""


# ---------------------------------------------------------------- scope loading

def load_scope(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Usage(f"cannot read scope file {path}: {exc}")
    if not isinstance(data, dict):
        raise Usage("scope file root must be an object")
    return data


def check_scope_shape(scope):
    problems = []
    for key in ("recon_targets", "out_of_scope", "rules"):
        if not isinstance(scope.get(key), dict):
            problems.append(f"{key} missing or not an object")
    rt = scope.get("recon_targets") if isinstance(scope.get("recon_targets"), dict) else {}
    if not any(rt.get(k) for k in ("domains", "wildcards", "urls", "api_urls")):
        problems.append("recon_targets has no domains, wildcards or urls")
    rules = scope.get("rules") if isinstance(scope.get("rules"), dict) else {}
    for name in ("automation", "ai_use", "rate_limit", "identification_header"):
        if name not in rules:
            problems.append(f"rules.{name} missing")
    return problems


def scope_rate_per_minute(scope):
    rate = (scope.get("rules") or {}).get("rate_limit") or {}
    if "value" not in rate:
        return None
    unit = rate.get("unit")
    if unit not in UNIT_TO_PER_MINUTE or not isinstance(rate["value"], (int, float)):
        raise Refusal("the scope's rate_limit has no usable unit; fix the scope file")
    return float(rate["value"]) * UNIT_TO_PER_MINUTE[unit]


def scope_header(scope):
    """The identification header the scope states, as (name, value) or None."""
    ident = (scope.get("rules") or {}).get("identification_header") or {}
    if ident.get("name") and ident.get("value"):
        return ident["name"], ident["value"]
    rh = scope.get("required_header")
    if isinstance(rh, dict) and rh.get("name") and rh.get("value"):
        return rh["name"], rh["value"]
    return None


def seeds_from_scope(scope):
    """Root domains to enumerate from, and the exact hosts the scope lists."""
    rt = scope.get("recon_targets") or {}
    roots, exact = [], []
    for w in rt.get("wildcards") or []:
        root = w.lstrip("*.").lower()
        if root and root not in roots:
            roots.append(root)
    for d in rt.get("domains") or []:
        h = d.lower()
        if h not in exact:
            exact.append(h)
    for u in (rt.get("urls") or []) + (rt.get("api_urls") or []):
        h = (urlparse(u).hostname or "").lower()
        if h and h not in exact:
            exact.append(h)
    return roots, exact


# ---------------------------------------------------------------- rules resolution

def resolve_rate(arg_rate, scope):
    cap = scope_rate_per_minute(scope)
    if arg_rate is None:
        if cap is None:
            raise Refusal("no --rate given and the scope states no rate limit; refusing to guess")
        return cap
    if arg_rate <= 0:
        raise Usage("--rate must be positive (requests per minute)")
    if cap is not None and arg_rate > cap:
        raise Refusal(f"--rate {arg_rate:g}/min is above the scope's rate of {cap:g}/min")
    return float(arg_rate)


def resolve_header(arg_header, no_identifier, scope, hosts):
    if arg_header:
        if ":" not in arg_header:
            raise Usage("--header must look like 'Name: value'")
        name, value = arg_header.split(":", 1)
        name, value = name.strip(), value.strip()
        if not name or not value:
            raise Usage("--header must look like 'Name: value'")
        stated = scope_header(scope)
        if stated and (name.lower(), value) != (stated[0].lower(), stated[1]):
            raise Refusal(f"--header does not match the scope's required header '{stated[0]}'")
        return name, value
    stated = scope_header(scope)
    if stated:
        return stated
    if no_identifier:
        if hosts and all(h in LOCAL_HOSTS for h in hosts):
            return None
        raise Refusal("--no-identifier-header is only for localhost targets")
    raise Refusal("no identification header: the scope states none and --header was not given")


# ---------------------------------------------------------------- filtering

def keep_in_scope(hosts, scope, label, dropped):
    kept = []
    for h in hosts:
        h = h.strip().lower().rstrip(".")
        if not h:
            continue
        if host_in_scope(h, scope):
            if h not in kept:
                kept.append(h)
        else:
            dropped.append((label, h))
    return kept


def oos_networks(scope):
    nets = []
    oos = scope.get("out_of_scope") or {}
    for key in ("ips", "cidrs"):
        for v in oos.get(key) or []:
            try:
                nets.append(ipaddress.ip_network(v.strip(), strict=False))
            except ValueError:
                pass
    return nets


def resolve_hosts(hosts, scope, live, resolved_map, dropped):
    """Second filter point: drop hosts that do not resolve, or resolve into out-of-scope space."""
    nets = oos_networks(scope)
    kept = []
    for h in hosts:
        ip = None
        if live:
            try:
                ip = socket.gethostbyname(h)
            except OSError:
                dropped.append(("resolution-failed", h))
                continue
        else:
            ip = resolved_map.get(h)
        if ip:
            try:
                addr = ipaddress.ip_address(ip)
                if any(addr.version == n.version and addr in n for n in nets):
                    dropped.append(("resolves-out-of-scope", f"{h} -> {ip}"))
                    continue
            except ValueError:
                pass
        kept.append(h)
    return kept


def host_of(address):
    parsed = urlparse(address if "://" in address else "//" + address)
    return (parsed.hostname or "").lower()


def filter_probe_rows(rows, scope, dropped):
    kept = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        urls = [row.get("url"), row.get("final_url"), row.get("location")]
        hosts = [host_of(u) for u in urls if isinstance(u, str) and u]
        if hosts and all(host_in_scope(h, scope) for h in hosts if h):
            kept.append(row)
        else:
            dropped.append(("probe", " ".join(u for u in urls if isinstance(u, str) and u)))
    return kept


# ---------------------------------------------------------------- commands

def find_tool(name):
    local = REPO_ROOT / "tools" / "bin" / name
    if local.is_file() and os.access(local, os.X_OK):
        return str(local)
    return shutil.which(name)


def build_commands(roots, hosts_file, rate_per_min, header, archive_hosts):
    """The exact argument lists. Header goes where a tool sends traffic to the target."""
    rpm = max(1, int(math.floor(rate_per_min)))
    cmds = []
    for root in roots:
        cmds.append(("subfinder", ["subfinder", "-d", root, "-silent", "-rate-limit-minute", str(rpm)]))
    probe = ["httpx", "-l", str(hosts_file), "-json", "-silent", "-threads", "1",
             "-rate-limit-minute", str(rpm)]
    if header:
        probe += ["-H", f"{header[0]}: {header[1]}"]
    cmds.append(("httpx", probe))
    for h in archive_hosts:
        cmds.append(("gau", ["gau", "--threads", str(GAU_THREADS), h]))
    return cmds


def run_cmd(argv, timeout=TOOL_TIMEOUT):
    exe = find_tool(argv[0])
    if not exe:
        raise Usage(f"{argv[0]} not found (see tools/install_tools.sh)")
    proc = subprocess.run([exe] + argv[1:], capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        print(f"warning: {argv[0]} exited {proc.returncode}: {proc.stderr.strip()[:200]}", file=sys.stderr)
    return proc.stdout


# ---------------------------------------------------------------- readers

def read_lines(path):
    try:
        return [l.strip() for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]
    except OSError:
        return None


def parse_json_rows(text):
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        rows = []
        for line in text.splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows


# ---------------------------------------------------------------- main flow

def main(argv=None):
    ap = argparse.ArgumentParser(description="Scope-bound passive recon.")
    ap.add_argument("--scope-json", required=True)
    ap.add_argument("--target-name", required=True)
    ap.add_argument("--output", help="default: recon_output/[target-name]")
    ap.add_argument("--rate", type=float, help="requests per minute; may not exceed the scope's rate")
    ap.add_argument("--header", help="'Name: value'; defaults to the scope's identification header")
    ap.add_argument("--no-identifier-header", action="store_true", help="localhost targets only")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--validate-scope-only", action="store_true")
    ap.add_argument("--fixture", metavar="DIR")
    args = ap.parse_args(argv)

    try:
        return run(args)
    except Usage as exc:
        print(f"usage error: {exc}", file=sys.stderr)
        return 2
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 3


def run(args):
    scope = load_scope(args.scope_json)
    problems = check_scope_shape(scope)
    if problems:
        for p in problems:
            print(f"scope problem: {p}", file=sys.stderr)
        return 1
    roots, exact = seeds_from_scope(scope)
    if args.validate_scope_only:
        print(f"scope OK for {args.target_name}")
        print(f"wildcard roots: {', '.join(roots) or 'none'}")
        print(f"exact hosts: {', '.join(exact) or 'none'}")
        cap = scope_rate_per_minute(scope)
        print(f"scope rate: {'unspecified' if cap is None else f'{cap:g} per minute'}")
        print(f"rules confirmed by human: {bool(scope['rules'].get('confirmed_by_human'))}")
        return 0

    rate = resolve_rate(args.rate, scope)
    header = resolve_header(args.header, args.no_identifier_header, scope, roots + exact)
    live = not args.dry_run and not args.fixture
    rules = scope["rules"]
    if live:
        if not rules.get("confirmed_by_human"):
            raise Refusal("rules.confirmed_by_human is false; run: python3 tools/scope_check.py confirm --target [target]")
        if (rules.get("automation") or {}).get("status") == "prohibited":
            raise Refusal("the program prohibits automated tools")
        if (rules.get("ai_use") or {}).get("status") in ("prohibited", "restricted"):
            raise Refusal("the program prohibits or restricts AI-assisted testing")

    out_root = Path(args.output) if args.output else REPO_ROOT / "recon_output" / args.target_name
    ts = os.environ.get("RECON_TS") or datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = out_root / ts
    dropped = []

    # Point 1: after enumeration.
    if args.fixture:
        fx = Path(args.fixture)
        if not fx.is_dir():
            raise Usage(f"fixture folder not found: {fx}")
        found = read_lines(fx / "subdomains.txt") or []
    elif args.dry_run:
        found = []
    else:
        found = []
        for root in roots:
            found += run_cmd(build_commands([root], "", rate, header, [])[0][1]).splitlines()
    candidates = list(exact) + [h for h in found if h not in exact]
    hosts = keep_in_scope(candidates, scope, "enumeration", dropped)

    # Point 2: after resolution.
    resolved_map = {}
    if args.fixture:
        rj = Path(args.fixture) / "resolved.json"
        if rj.is_file():
            resolved_map = json.loads(rj.read_text(encoding="utf-8"))
    hosts = resolve_hosts(hosts, scope, live, resolved_map, dropped)

    hosts_file = run_dir / "hosts.txt"
    cmds = build_commands(roots, hosts_file, rate, header, hosts)
    if args.dry_run:
        print(f"target: {args.target_name}")
        print(f"rate: {rate:g} per minute")
        print(f"header: {header[0] + ': ' + header[1] if header else 'none (localhost only)'}")
        print(f"in-scope hosts known before enumeration ({len(hosts)}):")
        for h in hosts:
            print(f"  {h}")
        print("commands (nothing is sent in a dry run):")
        for _, argv in cmds:
            print("  " + shlex.join(argv))
        print(f"output would go to: {run_dir}")
        return 0

    # Probe.
    if args.fixture:
        text = (Path(args.fixture) / "httpx_results.json")
        rows = parse_json_rows(text.read_text(encoding="utf-8")) if text.is_file() else []
        archive = read_lines(Path(args.fixture) / "archive_urls.txt") or []
    else:
        run_dir.mkdir(parents=True, exist_ok=True)
        hosts_file.write_text("\n".join(hosts) + "\n", encoding="utf-8")
        rows = parse_json_rows(run_cmd([a for n, a in cmds if n == "httpx"][0]))
        archive = []
        for n, a in cmds:
            if n == "gau":
                archive += run_cmd(a).splitlines()

    # Point 3: after probing (probe rows, redirects, archive URLs).
    rows = filter_probe_rows(rows, scope, dropped)
    probed_hosts = {host_of(r.get("url", "")) for r in rows}
    if args.fixture:
        rows = [r for r in rows if host_of(r.get("url", "")) in hosts]
    archive_kept = []
    for u in archive:
        h = host_of(u)
        if h and host_in_scope(h, scope):
            archive_kept.append(u)
        else:
            dropped.append(("archive", u))

    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "subdomains.txt").write_text("\n".join(hosts) + ("\n" if hosts else ""), encoding="utf-8")
    (run_dir / "httpx_results.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    (run_dir / "archive_urls.txt").write_text("\n".join(archive_kept) + ("\n" if archive_kept else ""), encoding="utf-8")
    (run_dir / "dropped_out_of_scope.txt").write_text(
        "".join(f"{label}\t{item}\n" for label, item in dropped), encoding="utf-8")
    (run_dir / "run_meta.json").write_text(json.dumps({
        "target": args.target_name, "mode": "fixture" if args.fixture else "live",
        "rate_per_minute": rate, "header_name": header[0] if header else None,
        "hosts": len(hosts), "live_rows": len(rows), "archive_urls": len(archive_kept),
        "dropped": len(dropped), "probed_hosts": sorted(h for h in probed_hosts if h)}, indent=2) + "\n",
        encoding="utf-8")
    print(f"wrote {run_dir}: {len(hosts)} hosts, {len(rows)} live, {len(archive_kept)} archive urls, "
          f"{len(dropped)} dropped as out of scope")
    return 0


if __name__ == "__main__":
    sys.exit(main())
