#!/usr/bin/env bash
#
# start_workflow.sh — 3-window tmux workflow with a window-confined Claude Code swarm.
#
#   Window "Local"   local shell
#   Window "Remote"  ssh to the desktop (placeholders below)
#   Window "Swarm"   Claude Code lead agent; teammates split INTO this window
#
# Never touches ~/.tmux.conf. Reads it implicitly via the running server only.
#
# Usage:
#   ./start_workflow.sh                        # create or attach
#   ./start_workflow.sh --no-settings          # never touch settings.json (flag-only mode)
#   ./start_workflow.sh --kill                 # tear the session down
#   ./start_workflow.sh --doctor               # preflight checks, create nothing
#   REMOTE_USER=ais REMOTE_HOST=10.0.0.5 ./start_workflow.sh
#
set -euo pipefail

# ---------------------------------------------------------------- configuration
SESSION="${WORKFLOW_SESSION:-Lappy}"
REMOTE_USER="${REMOTE_USER:-ais}"
REMOTE_HOST="${REMOTE_HOST:-YOUR_DESKTOP_IP}"
WORK_DIR="${WORKFLOW_CWD:-$PWD}"
SETTINGS="${CLAUDE_SETTINGS:-$HOME/.claude/settings.json}"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
INSTRUCTIONS="${SWARM_INSTRUCTIONS:-$SCRIPT_DIR/swarm_instructions.txt}"

WRITE_SETTINGS=1
MODE="up"

for arg in "$@"; do
  case "$arg" in
    --no-settings) WRITE_SETTINGS=0 ;;
    --kill)        MODE="kill" ;;
    --doctor)      MODE="doctor" ;;
    -h|--help)     sed -n '3,18p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) printf 'unknown argument: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

die()  { printf '\033[31merror\033[0m  %s\n' "$*" >&2; exit 1; }
note() { printf '\033[36m··\033[0m %s\n' "$*"; }
ok()   { printf '\033[32mok\033[0m     %s\n' "$*"; }
warn() { printf '\033[33mwarn\033[0m   %s\n' "$*"; }

# ---------------------------------------------------------------- preflight
preflight() {
  command -v tmux >/dev/null   || die "tmux not found in PATH"
  command -v claude >/dev/null || die "claude not found in PATH"
  [ -r "$INSTRUCTIONS" ]       || die "missing bootstrap prompt: $INSTRUCTIONS"

  # tmux -e (per-window environment) needs >= 3.0. Cheaper to assert than to fail
  # opaquely inside a detached window whose output nobody reads.
  local ver major minor
  ver="$(tmux -V | awk '{print $2}')"
  major="${ver%%.*}"; minor="${ver#*.}"; minor="${minor//[!0-9]/}"
  if [ "${major:-0}" -lt 3 ]; then
    die "tmux $ver is too old; 'new-window -e' needs >= 3.0"
  fi
  ok "tmux $ver, claude present, bootstrap prompt readable"

  # settings.json env beats the shell export, so a stale 0 there silently wins.
  if [ -r "$SETTINGS" ] && command -v python3 >/dev/null; then
    python3 - "$SETTINGS" <<'PY' || true
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as e:
    print(f"warn   settings.json unparseable ({e}); skipping precedence check")
    sys.exit(0)
teams = (d.get("env") or {}).get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS")
if teams not in (None, "1"):
    print(f"warn   settings.json env pins AGENT_TEAMS={teams!r}; it OVERRIDES the shell export")
mode = d.get("teammateMode")
print(f"··  teammateMode currently: {mode!r}" if mode else "··  teammateMode unset (defaults to in-process)")
PY
  fi
}

# ------------------------------------------------- settings.json (idempotent)
# Split panes require teammateMode. The --teammate-mode flag is passed per-session
# regardless; this only persists the preference, and only when it differs.
ensure_settings() {
  [ "$WRITE_SETTINGS" -eq 1 ] || { note "skipping settings.json (--no-settings)"; return 0; }
  command -v python3 >/dev/null || { warn "python3 absent; relying on --teammate-mode flag only"; return 0; }

  python3 - "$SETTINGS" <<'PY'
import json, os, shutil, sys, tempfile, time

path = sys.argv[1]
os.makedirs(os.path.dirname(path), exist_ok=True)

try:
    with open(path) as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON is not an object")
except FileNotFoundError:
    data = {}
except Exception as e:
    # Never clobber a file we could not parse. The CLI flag still carries us.
    print(f"warn   {path} unreadable ({e}); leaving it untouched")
    sys.exit(0)

if data.get("teammateMode") == "tmux":
    print("ok     teammateMode already 'tmux'")
    sys.exit(0)

backup = f"{path}.bak.{time.strftime('%Y%m%d-%H%M%S')}"
if os.path.exists(path):
    shutil.copy2(path, backup)
    print(f"··  backed up -> {backup}")

previous = data.get("teammateMode")
data["teammateMode"] = "tmux"

# Atomic replace: a half-written settings.json breaks every future session.
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
with os.fdopen(fd, "w") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")
os.replace(tmp, path)
print(f"ok     teammateMode {previous!r} -> 'tmux'")
PY
}

# ---------------------------------------------------------------- attach logic
# attach-session fails from inside tmux; switch-client is the nested-safe form.
attach() {
  if [ -n "${TMUX:-}" ]; then
    note "already inside tmux; switching client"
    tmux switch-client -t "$SESSION"
  elif [ -t 1 ]; then
    tmux attach-session -t "$SESSION"
  else
    # No controlling terminal (CI, pipe, subagent shell). Building the session is
    # the useful half; attaching would just fail with "open terminal failed".
    note "not a tty; session left detached — attach with: tmux attach -t $SESSION"
  fi
}

# ---------------------------------------------------------------- teardown
if [ "$MODE" = "kill" ]; then
  tmux has-session -t "$SESSION" 2>/dev/null || die "no session named '$SESSION'"
  tmux kill-session -t "$SESSION"
  ok "killed session '$SESSION'"
  exit 0
fi

if [ "$MODE" = "doctor" ]; then
  preflight
  tmux has-session -t "$SESSION" 2>/dev/null \
    && ok "session '$SESSION' exists" \
    || note "session '$SESSION' not created yet"
  exit 0
fi

# ---------------------------------------------------------------- build or attach
preflight

if tmux has-session -t "$SESSION" 2>/dev/null; then
  ok "session '$SESSION' exists; attaching (windows left untouched)"
  attach
  exit 0
fi

ensure_settings

note "building session '$SESSION' in $WORK_DIR"

# Windows are addressed BY NAME throughout. This config sets renumber-windows on
# and base-index 1, so positional indices shift whenever a window closes.
tmux new-session -d -s "$SESSION" -n LOCAL -c "$WORK_DIR"

# --- Window: Remote ----------------------------------------------------------
# Keep the window alive after ssh exits, so a dropped link leaves a usable shell
# instead of collapsing the window and renumbering everything after it.
if [ "$REMOTE_HOST" = "YOUR_DESKTOP_IP" ]; then
  warn "REMOTE_HOST is still a placeholder; Remote opens a local shell with a hint"
  tmux new-window -t "$SESSION:" -n REMOTE -c "$WORK_DIR" \
    "printf 'Set REMOTE_USER and REMOTE_HOST, then: ssh \$REMOTE_USER@\$REMOTE_HOST\n\n'; exec \"\$SHELL\""
else
  tmux new-window -t "$SESSION:" -n REMOTE -c "$WORK_DIR" \
    "ssh ${REMOTE_USER}@${REMOTE_HOST} || printf '\nssh exited (%s). Shell below.\n' \"\$?\"; exec \"\$SHELL\""
fi

# --- Window: Swarm -----------------------------------------------------------
# 'new-window -e' injects environment natively — no shell-rc edits, no wrapper
# script, and no leakage into the other two windows.
#
# The lead is launched with:
#   --teammate-mode tmux        per-session override; beats settings.json
#   --append-system-prompt      doctrine as SYSTEM instructions, not a user turn
# The positional prompt slot is left free for the actual task.
#
# 'exec "$SHELL"' keeps the window alive when the lead exits, so teardown is
# deliberate rather than a window vanishing mid-run.
tmux new-window -t "$SESSION:" -n SWARM -c "$WORK_DIR" \
  -e CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 \
  "claude --teammate-mode tmux --append-system-prompt \"\$(cat '$INSTRUCTIONS')\" || printf '\nlead exited (%s). Shell below.\n' \"\$?\"; exec \"\$SHELL\""

tmux select-window -t "$SESSION:SWARM"

ok "session '$SESSION' ready: LOCAL | REMOTE | SWARM"
attach
