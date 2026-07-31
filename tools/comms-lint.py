#!/usr/bin/env python3
"""comms-lint: deterministic heuristic linter for agent-to-agent messages.

Checks a message against the comms standard: 10 violation categories, scored
as violations per 100 words (2 decimals), so short and long messages compare.

Fenced code blocks (``` ... ```) and 4-space-indented blocks are stripped
before scanning: verbatim command output and code are quoted evidence, not
prose, and are never scored. Inline backtick spans are NOT stripped (they
stay in the text) but they do satisfy the vague_referent exception below.

The single most important behavior: vague_referent ("the file", "the above",
...) is suppressed when the SAME sentence carries a resolvable referent — a
path/like/this.ext token, a file.ext:123 token, a backtick-quoted span, or an
absolute path starting with /.

CLI:
    python3 tools/comms-lint.py [FILE ...] [--mode report|message]
                                [--max-score FLOAT] [--show] [--json]

--show prints one line per violation after the summary:
    <line>:<category>: <matched text, trimmed to 60 chars>
Line numbers are 1-indexed against the ORIGINAL input text; --show never
changes the score, the exit code, or --json output.

Exit code 0 when score <= --max-score and no missing status line; 1
otherwise, so the tool works as an acceptance-criteria command.

Verify: cd repo root && python3 -m unittest discover -s tools -p 'test_*.py'
"""

import argparse
import json
import re
import sys

CATEGORY_IDS = [
    "long_sentence",
    "passive_voice",
    "nominalization",
    "phrasal_verb",
    "marketing_adjective",
    "hedge_opener",
    "banned_word",
    "vague_referent",
    "vague_quantifier",
    "long_paragraph",
]

# --- wordlists -----------------------------------------------------------
# phrasal_verb, marketing_adjective and the hedge_opener core are inherited
# from ste-lint.py; hedge_opener adds the six openers the standard names.
# banned_word is the substitution-table list plus common inflections, so
# inflected uses ("utilized", "leveraging") are caught along with the forms
# the standard lists.

PHRASAL_VERBS = [
    "spin up", "spin down", "reach out", "dive into", "dives into",
    "diving into", "kick off", "kicks off", "roll out", "rolls out",
    "tear down", "ramp up", "circle back", "drill down", "spun up",
    "reaching out",
]

MARKETING_ADJECTIVES = [
    "seamless", "seamlessly", "robust", "powerful", "cutting-edge",
    "effortless", "effortlessly", "world-class", "next-generation",
    "revolutionary", "blazing", "lightning-fast", "elegant", "delightful",
    "turnkey", "best-in-class", "state-of-the-art", "game-changing",
    "first-class", "battle-tested", "enterprise-grade", "supercharge",
    "unlock", "unleash", "empower", "empowers",
]

HEDGE_OPENERS = [
    "it is important to note", "it should be noted", "it is worth noting",
    "please note that", "as mentioned", "as noted above",
    "i think", "i believe", "it seems", "presumably", "arguably",
    "in my opinion",
]

BANNED_WORDS = [
    "utilize", "utilizes", "utilized", "utilizing",
    "leverage", "leverages", "leveraged", "leveraging",
    "facilitate", "facilitates", "facilitated", "facilitating",
    "ensure", "ensures", "ensured", "ensuring",
    "prior to", "subsequent to",
    "regarding",
    "obtain", "obtains", "obtained", "obtaining",
    "demonstrate", "demonstrates", "demonstrated", "demonstrating",
    "additionally", "furthermore", "moreover",
]

VAGUE_REFERENTS = [
    "the file", "this file", "that file", "the function", "this function",
    "the script", "the above", "as mentioned", "as noted above",
    "the aforementioned", "the former", "the latter", "earlier in this",
]

VAGUE_QUANTIFIERS = [
    "several", "many", "numerous", "various", "a few", "a couple",
    "roughly", "approximately",
]

# --- code stripping ------------------------------------------------------
# Stripped lines are replaced with EMPTY lines, never deleted, so line
# numbers in the stripped text match the original input 1:1; stripped
# regions simply score nothing (empty lines contribute no words or
# sentences).

FENCE_LINE = re.compile(r"^\s*```")
INDENTED_LINE = re.compile(r"^[ \t]{4,}")


def strip_code(text):
    """Blank fenced code lines and 4-space-indented lines.

    Inline backtick spans are deliberately NOT removed: they stay as text
    and satisfy the vague_referent resolvable-referent exception.
    """
    lines = text.split("\n")
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_LINE.match(line):
            if line.count("```") % 2 == 1:  # one marker toggles; "```x```" is balanced
                in_fence = not in_fence
            lines[i] = ""
        elif in_fence:
            lines[i] = ""
        elif INDENTED_LINE.match(line):
            lines[i] = ""
    return "\n".join(lines)


# --- sentence splitting --------------------------------------------------
# Split on [.!?] followed by whitespace or end-of-string. Before splitting,
# the dots in decimals, ellipses and e.g./i.e./etc./vs./Dr./No. are replaced
# with a NUL sentinel so they never read as sentence ends; restored after.

DECIMAL = re.compile(r"\d+\.\d+")
ELLIPSIS = re.compile(r"\.\.\.")
# Letter-based lookarounds, not \b: the trailing char after "e.g." is
# whitespace, so a word boundary can never exist after the final period.
ABBREV = re.compile(r"(?<![a-z])(?:e\.g\.|i\.e\.|etc\.|vs\.|Dr\.|No\.)(?![a-z])", re.I)
SENT_SPLIT = re.compile(r"[.!?](?:\s+|$)")


def _protect_dots(text):
    for pat in (DECIMAL, ELLIPSIS, ABBREV):
        text = pat.sub(lambda m: m.group(0).replace(".", "\x00"), text)
    return text


def split_sentence_spans(text):
    """Split text into (sentence, start_offset) pairs.

    The start offset is a character index valid against `text` itself, so
    callers can map each sentence back to its original line number.
    """
    protected = _protect_dots(text)
    out = []
    last = 0
    for m in SENT_SPLIT.finditer(protected):
        part = protected[last:m.start()]
        stripped = part.replace("\x00", ".").strip()
        if stripped:
            out.append((stripped, last + len(part) - len(part.lstrip())))
        last = m.end()
    tail = protected[last:]
    if tail.strip():
        stripped = tail.replace("\x00", ".").strip()
        out.append((stripped, last + len(tail) - len(tail.lstrip())))
    return out


def split_sentences(text):
    """Split text into sentences using the [.!?]+whitespace rule."""
    return [s for s, _ in split_sentence_spans(text)]


# --- per-category patterns -----------------------------------------------

BE_VERB = r"(?:is|are|was|were|be|been|being)"
PP_IRREG = (r"(?:done|made|found|given|taken|seen|written|run|read|built|"
            r"held|kept|sent|set|put|left|lost|met|paid|told)")
# Be-verb followed within 2 words by a past participle. Kept deliberately
# narrow: a noisy linter gets ignored, precision beats recall.
PASSIVE_RE = re.compile(
    rf"\b{BE_VERB}\s+(?:\S+\s+)?(?:[a-z]{{2,}}ed|{PP_IRREG})\b", re.I
)

NOMINALIZATION_RE = re.compile(
    r"\b(?:perform|conduct|provide|carry out|make|do)\s+"
    r"(?:(?:a|an|the)\s+)?[a-z]{2,}(?:tion|ment|ance|ence|sis|ing)\b",
    re.I,
)

VAGUE_REFERENT_RE = re.compile(
    r"(?<![a-z])(?:" + "|".join(re.escape(p) for p in VAGUE_REFERENTS) + r")(?![a-z])",
    re.I,
)

# Resolvable referents that satisfy the vague_referent exception:
#   path/like/this.ext | file.ext:123 | `backtick span` | /absolute/path
REFERENT_RE = re.compile(
    r"[\w./-]+/[\w./-]+\.\w{1,6}\b"
    r"|\b[\w.-]+\.\w{1,6}:\d+\b"
    r"|`[^`]*`"
    r"|(?<!\S)/\S+"
)

VAGUE_QUANTIFIER_RE = re.compile(
    r"(?<![a-z])(?:" + "|".join(re.escape(p) for p in VAGUE_QUANTIFIERS) + r")(?![a-z])"
    r"|(?<![a-z])about\s*(?=\d)",
    re.I,
)

# --- status line (mode report, structural check) -------------------------

STATUS_ANY = re.compile(r"status:", re.I)
STATUS_WORD = re.compile(
    r"(?<![a-z])(?:done|blocked|partial|confirmed|refuted|uncertain)(?![a-z])",
    re.I,
)


def check_status_line(text):
    """True when the first non-empty line carries no status marker."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        return not (STATUS_ANY.search(line) or STATUS_WORD.search(line))
    return True  # no non-empty line at all


# --- linting -------------------------------------------------------------

def phrase_matches(text, phrases):
    """Case-insensitive whole-phrase matches; yields (phrase, (start, end))."""
    low = text.lower()
    for ph in phrases:
        pat = r"(?<![a-z])" + re.escape(ph) + r"(?![a-z])"
        for m in re.finditer(pat, low):
            yield ph, m.span()


def para_spans(text):
    """Split text into (paragraph, start_offset) on blank-line boundaries."""
    out = []
    last = 0
    for m in re.finditer(r"\n\s*\n", text):
        part = text[last:m.start()]
        stripped = part.strip()
        if stripped:
            out.append((stripped, last + len(part) - len(part.lstrip())))
        last = m.end()
    tail = text[last:]
    if tail.strip():
        out.append((tail.strip(), last + len(tail) - len(tail.lstrip())))
    return out


def line_of(text, offset):
    """1-indexed line number of character `offset` in `text`."""
    return text.count("\n", 0, offset) + 1


def display_text(text):
    """Collapse whitespace and trim to 60 chars for --show output."""
    return re.sub(r"\s+", " ", text.strip())[:60]


def _record(locations, counts, stripped, offset, cid, matched):
    """Register one violation: count it and store its (line, category, text)."""
    counts[cid] += 1
    locations.append((line_of(stripped, offset), cid, display_text(matched)))


def lint_text(text, mode="message"):
    """Produce the full result dict for one combined message.

    The dict carries an extra "locations" key: (line, category, matched text
    trimmed to 60 chars), sorted at print time. The CLI strips it before
    JSON output so --json keeps its exact shape.
    """
    stripped = strip_code(text)
    words = len(stripped.split())

    counts = {cid: 0 for cid in CATEGORY_IDS}
    locations = []

    for sent, start in split_sentence_spans(stripped):
        if len(sent.split()) > 20:
            _record(locations, counts, stripped, start, "long_sentence", sent)
        for m in PASSIVE_RE.finditer(sent):
            _record(locations, counts, stripped, start + m.start(), "passive_voice", m.group(0))
        for m in NOMINALIZATION_RE.finditer(sent):
            _record(locations, counts, stripped, start + m.start(), "nominalization", m.group(0))
        for ph, (a, _b) in phrase_matches(sent, PHRASAL_VERBS):
            _record(locations, counts, stripped, start + a, "phrasal_verb", ph)
        for ph, (a, _b) in phrase_matches(sent, MARKETING_ADJECTIVES):
            _record(locations, counts, stripped, start + a, "marketing_adjective", ph)
        for ph, (a, _b) in phrase_matches(sent, HEDGE_OPENERS):
            _record(locations, counts, stripped, start + a, "hedge_opener", ph)
        for ph, (a, _b) in phrase_matches(sent, BANNED_WORDS):
            _record(locations, counts, stripped, start + a, "banned_word", ph)
        # The rule-8 exception: a resolvable referent in the SAME sentence
        # suppresses vague_referent. Flagging "the file src/main.py:42 is
        # stale" as vague would be actively harmful, so this is per-sentence.
        if VAGUE_REFERENT_RE.search(sent) and not REFERENT_RE.search(sent):
            for m in VAGUE_REFERENT_RE.finditer(sent):
                _record(locations, counts, stripped, start + m.start(), "vague_referent", m.group(0))
        for m in VAGUE_QUANTIFIER_RE.finditer(sent):
            _record(locations, counts, stripped, start + m.start(), "vague_quantifier", m.group(0))
    for para, start in para_spans(stripped):
        if len(split_sentences(para)) > 6:
            _record(locations, counts, stripped, start, "long_paragraph", para)

    total = sum(counts.values())
    score = round(total * 100.0 / words, 2) if words else 0.0
    missing_status = check_status_line(text) if mode == "report" else None
    return {
        "counts": counts,
        "total": total,
        "words": words,
        "score": score,
        "missing_status_line": missing_status,
        "locations": locations,
    }


# --- CLI -----------------------------------------------------------------

def print_human(result):
    for cid in CATEGORY_IDS:
        if result["counts"][cid]:
            print(f"{cid}: {result['counts'][cid]}")
    print(f"total: {result['total']}")
    print(f"words: {result['words']}")
    print(f"score: {result['score']:.2f} violations/100 words")
    if result["missing_status_line"]:
        print("missing_status_line: true")


def main(argv=None, stdin=None):
    parser = argparse.ArgumentParser(
        prog="comms-lint",
        description="Deterministic heuristic linter for agent-to-agent messages.",
    )
    parser.add_argument("files", nargs="*", metavar="FILE",
                        help="files to lint (default: stdin; multiple files are combined)")
    parser.add_argument("--mode", choices=("report", "message"), default="message",
                        help="report mode also checks the first line for a status marker")
    parser.add_argument("--max-score", type=float, default=3.0,
                        help="exit 1 when score exceeds this (default 3.0)")
    parser.add_argument("--show", action="store_true",
                        help="after the summary, print one line per violation: "
                             "line:category: matched text")
    parser.add_argument("--json", action="store_true",
                        help="emit one JSON object instead of human-readable output")
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    if args.files:
        chunks = []
        for path in args.files:
            with open(path, encoding="utf-8") as fh:
                chunks.append(fh.read())
        text = "\n".join(chunks)
    else:
        stream = stdin if stdin is not None else sys.stdin
        text = stream.read()

    result = lint_text(text, args.mode)
    if args.json:
        print(json.dumps({k: v for k, v in result.items() if k != "locations"}))
    else:
        print_human(result)
        if args.show:
            for line, cid, matched in sorted(result["locations"], key=lambda x: (x[0], x[1])):
                print(f"{line}:{cid}: {matched}")

    failed = result["score"] > args.max_score or bool(result["missing_status_line"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
