#!/usr/bin/env python3
"""codemap.py -- deterministic, model-free structural code map.

Signature-level extraction of source files plus honest size-based token
estimates.  Stdlib only.  Regex-based on purpose: never crashes on weird
input, output is deterministic and greppable.

Interface:
    python3 codemap.py PATH [PATH...] [--tree] [--json] [--exclude PAT ...]

Exit 0 on success (even when individual files were unsupported), exit 2
only on bad CLI arguments or a path that does not exist.
"""

import fnmatch
import json
import os
import re
import sys

# --------------------------------------------------------------------------
# Language table
# --------------------------------------------------------------------------

EXT_LANG = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.mjs': 'javascript',
    '.cjs': 'javascript',
    '.go': 'go',
    '.rs': 'rust',
    '.java': 'java',
    '.kt': 'kotlin',
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.cc': 'cpp',
    '.hpp': 'cpp',
    '.rb': 'ruby',
    '.php': 'php',
    '.swift': 'swift',
    '.sh': 'shell',
    '.bash': 'shell',
    '.zsh': 'shell',
    '.md': 'markdown',
    '.markdown': 'markdown',
}

# (line_comment_starts, block_open, block_close, use_backtick_strings,
#  triple_quote_markers)
COMMENT_STYLES = {
    'python':     (('#',), None, None, False, ('"""', "'''")),
    'ruby':       (('#',), None, None, False, ()),
    'shell':      (('#',), None, None, False, ()),
    'markdown':   ((), None, None, False, ()),
    'javascript': (('//',), '/*', '*/', True, ()),
    'typescript': (('//',), '/*', '*/', True, ()),
    'go':         (('//',), '/*', '*/', True, ()),
    'rust':       (('//',), '/*', '*/', True, ()),
    'java':       (('//',), '/*', '*/', False, ()),
    'kotlin':     (('//',), '/*', '*/', False, ()),
    'c':          (('//',), '/*', '*/', False, ()),
    'cpp':        (('//',), '/*', '*/', False, ()),
    'php':        (('//', '#'), '/*', '*/', False, ()),
    'swift':      (('//',), '/*', '*/', False, ()),
}

# Per-language sets of symbol kinds that own indented/braced children.
CONTAINERS = {
    'python': {'class', 'def'},
    'ruby': {'class', 'module', 'def'},
    'shell': set(),
    'javascript': {'class'},
    'typescript': {'class'},
    'go': {'struct', 'interface', 'type'},
    'rust': {'struct', 'enum', 'trait', 'impl', 'mod'},
    'java': {'class', 'interface', 'enum', 'record'},
    'kotlin': {'class', 'interface', 'enum', 'record', 'object'},
    'c': {'struct', 'class', 'enum', 'union'},
    'cpp': {'struct', 'class', 'enum', 'union'},
    'php': {'class', 'interface', 'trait'},
    'swift': {'class', 'struct', 'enum', 'protocol', 'extension'},
    'markdown': set(),
}

# Symbol kinds whose map-block display is the trimmed signature rather than
# the "kind name" form (e.g. "def bar(self, x)" not "def bar").
SIG_KINDS = {'def', 'fn', 'fun', 'func', 'method', 'function', 'fn?',
             'heading', 'impl'}

JS_KEYWORDS = {
    'if', 'for', 'while', 'switch', 'catch', 'return', 'import', 'export',
    'class', 'type', 'interface', 'function', 'new', 'delete', 'typeof',
    'instanceof', 'else', 'do', 'try', 'finally', 'with', 'case', 'throw',
    'in', 'of', 'await', 'async', 'yield', 'default', 'break', 'continue',
    'var', 'let', 'const', 'extends', 'implements', 'super', 'this', 'void',
}

C_KEYWORDS = {
    'if', 'for', 'while', 'switch', 'return', 'sizeof', 'do', 'else', 'case',
    'goto', 'static_assert', '_Static_assert', 'alignof', 'typeof',
    'typeof_unqual',
}

SKIP_DIRS = {'node_modules', '__pycache__', 'vendor', 'dist', 'build',
             'target', '.git'}

SIG_CAP = 120
MB_THRESHOLD = 1_000_000
IMPORT_CAP = 20

# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------


def clean_sig(code):
    """Trim a declaration line: strip, drop trailing { : ;, cap at 120."""
    s = code.strip()
    s = re.sub(r'[{:;]\s*$', '', s)
    s = s.rstrip()
    if len(s) > SIG_CAP:
        s = s[:SIG_CAP] + '…'
    return s


def fmt_tokens(n):
    """Size-based estimate, honestly labelled. None means unknown -> pending."""
    if n is None:
        return 'tokens: pending'
    if n < 1000:
        return '{} tok'.format(n)
    if n < 1_000_000:
        return '~{:.1f}k tok'.format(n / 1000.0)
    return '~{:.2f}M tok'.format(n / 1_000_000.0)


def lang_for(path):
    _, ext = os.path.splitext(path)
    return EXT_LANG.get(ext.lower())


def count_lines(path):
    with open(path, 'rb') as f:
        return sum(1 for _ in f)


def dedup_cap(items, cap=IMPORT_CAP):
    """Dedupe preserving first-appearance order, cap at N then '...'."""
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    if len(out) > cap:
        return out[:cap] + ['...']
    return out


# --------------------------------------------------------------------------
# Comment/string-aware code-span extraction
# --------------------------------------------------------------------------


def code_spans(line, style, state):
    """Return (spans, new_state) for the runnable-code portions of a line.

    spans is a list of (start, end) offsets that are NOT inside a string or
    comment.  state carries string/comment state across lines (multi-line
    block comments, backtick strings, triple-quoted strings).
    """
    line_comments, block_open, block_close, use_backtick, triples = style
    spans = []
    start = None
    i = 0
    n = len(line)
    while i < n:
        ch = line[i]
        if state == 'code':
            if start is None:
                start = i
            matched = False
            for c in line_comments:
                if line.startswith(c, i):
                    if start is not None:
                        spans.append((start, i))
                        start = None
                    state = 'linecomment'
                    i += len(c)
                    matched = True
                    break
            if matched:
                continue
            if block_open and line.startswith(block_open, i):
                if start is not None:
                    spans.append((start, i))
                    start = None
                state = 'blockcomment'
                i += len(block_open)
                continue
            if triples:
                entered = False
                for tq in triples:
                    if line.startswith(tq, i):
                        if start is not None:
                            spans.append((start, i))
                            start = None
                        state = ('tstr', tq)
                        i += len(tq)
                        entered = True
                        break
                if entered:
                    continue
            if ch in ('"', "'") or (use_backtick and ch == '`'):
                if start is not None:
                    spans.append((start, i))
                    start = None
                state = ('str', ch)
                i += 1
                continue
            i += 1
        elif isinstance(state, tuple):
            if state[0] == 'str':
                q = state[1]
                if ch == '\\' and i + 1 < n:
                    i += 2
                    continue
                if ch == q:
                    state = 'code'
                i += 1
            elif state[0] == 'tstr':
                tq = state[1]
                if line.startswith(tq, i):
                    state = 'code'
                    i += len(tq)
                    continue
                if ch == '\\' and i + 1 < n:
                    i += 2
                    continue
                i += 1
        elif state == 'linecomment':
            i = n
        elif state == 'blockcomment':
            if block_close and line.startswith(block_close, i):
                state = 'code'
                i += len(block_close)
                continue
            i += 1
    # A line comment cannot span lines; reset so the next line is code.
    if state == 'linecomment':
        state = 'code'
    if state == 'code' and start is not None:
        spans.append((start, n))
    return spans, state


def analyze_lines(text, lang):
    """Return (raw_lines, code_lines, depths).

    depths[i] is the nesting indent of line i: leading whitespace for
    indentation languages, brace depth otherwise.
    """
    style = COMMENT_STYLES.get(lang, ((), None, None, False, ()))
    raw_lines = text.splitlines()
    code_lines = []
    depths = []
    state = 'code'
    depth = 0
    for raw in raw_lines:
        if lang in ('python', 'ruby', 'shell'):
            expanded = raw.expandtabs(4)
            depths.append(len(expanded) - len(expanded.lstrip(' ')))
            spans, state = code_spans(raw, style, state)
            code_lines.append(''.join(raw[s:e] for s, e in spans))
        else:
            depths.append(depth)
            spans, state = code_spans(raw, style, state)
            code = ''.join(raw[s:e] for s, e in spans)
            code_lines.append(code)
            depth += code.count('{') - code.count('}')
    return raw_lines, code_lines, depths


# --------------------------------------------------------------------------
# Per-language symbol extractors.  Each returns (symbols, imports).
# A symbol dict: {kind, name, line, signature, indent, [level]}.
# --------------------------------------------------------------------------


def extract_python(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        if not s:
            continue
        if s.startswith('import '):
            body = s[len('import '):]
            for part in body.split(','):
                top = part.split('.')[0].split(' as ')[0].strip()
                if top:
                    imports.append(top)
                    syms.append({'kind': 'import', 'name': top, 'line': idx,
                                 'signature': clean_sig(code), 'indent': d})
            continue
        if s.startswith('from '):
            m = re.match(r'from\s+\.*([A-Za-z_]\w*)', s)
            if m:
                top = m.group(1)
                imports.append(top)
                syms.append({'kind': 'import', 'name': top, 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:async\s+)?(class|def)\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        if d == 0:
            m = re.match(r'^([A-Z][A-Z0-9_]*)\s*(?::[^=]*)?\s*=(?!=)', s)
            if m:
                syms.append({'kind': 'const', 'name': m.group(1), 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
    return syms, imports


def extract_jsts(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        if not s:
            continue
        # Modules are quoted strings, which code_spans strips; extract from
        # the raw line, but only when the line contains real code (the empty
        # check above already ran).  Detection is anchored to import/export
        # syntax so a bare string literal cannot fake an import.
        m = re.search(r'^\s*(?:import|export)\b.*?\bfrom\s*[\'"]([^\'"]+)[\'"]', raw)
        if m:
            mod = m.group(1)
            imports.append(mod)
            syms.append({'kind': 'import', 'name': mod, 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^\s*import\s*[\'"]([^\'"]+)[\'"]', raw)
        if m:
            mod = m.group(1)
            imports.append(mod)
            syms.append({'kind': 'import', 'name': mod, 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        rm = re.search(r'\brequire\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', raw)
        if rm:
            mod = rm.group(1)
            imports.append(mod)
            syms.append({'kind': 'import', 'name': mod, 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.search(r'\bclass\s+([A-Za-z_$][\w$]*)', s)
        if m:
            syms.append({'kind': 'class', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.search(r'\binterface\s+([A-Za-z_$][\w$]*)', s)
        if m:
            syms.append({'kind': 'interface', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.search(r'\btype\s+([A-Za-z_$][\w$]*)\s*=', s)
        if m:
            syms.append({'kind': 'type', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.search(r'\benum\s+([A-Za-z_$][\w$]*)', s)
        if m:
            syms.append({'kind': 'enum', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.search(r'\bfunction\s+([A-Za-z_$][\w$]*)\s*\(', s)
        if m:
            syms.append({'kind': 'function', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(', s)
        if m:
            syms.append({'kind': 'function', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        if d > 0:
            m = re.match(r'^(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^)]*\)[^{}]*\{', s)
            if m and m.group(1) not in JS_KEYWORDS:
                syms.append({'kind': 'method', 'name': m.group(1), 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
    return syms, imports


def extract_go(raw_lines, code_lines, depths):
    syms = []
    imports = []
    block = None  # 'import' | 'const' | 'var' | None
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        # Import specifiers are quoted strings, so code_spans empties them;
        # check the block state before the empty-line skip and read the
        # module from the raw line.
        if block == 'import':
            if s == ')':
                block = None
                continue
            m = re.search(r'["`]([^"`]+)["`]', raw)
            if m:
                mod = m.group(1).split('/')[-1]
                imports.append(mod)
                syms.append({'kind': 'import', 'name': mod, 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
            continue
        if not s:
            continue
        if block in ('const', 'var'):
            if s == ')':
                block = None
                continue
            m = re.match(r'([A-Za-z_]\w*)', s)
            if m:
                syms.append({'kind': block, 'name': m.group(1), 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
            continue
        if s.startswith('import'):
            if s.endswith('('):
                block = 'import'
                continue
            m = re.search(r'["`]([^"`]+)["`]', raw)
            if m:
                mod = m.group(1).split('/')[-1]
                imports.append(mod)
                syms.append({'kind': 'import', 'name': mod, 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(const|var)\s*\(\s*$', s)
        if m:
            block = m.group(1)
            continue
        m = re.match(r'^(const|var)\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^func\s+\(([^)]*)\)\s+([A-Za-z_]\w*)\s*\(', s)
        if m:
            syms.append({'kind': 'method', 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^func\s+([A-Za-z_]\w*)\s*\(', s)
        if m:
            syms.append({'kind': 'func', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^type\s+([A-Za-z_]\w*)\s+', s)
        if m:
            rest = s[m.end():].strip()
            if rest.startswith('struct'):
                kind = 'struct'
            elif rest.startswith('interface'):
                kind = 'interface'
            else:
                kind = 'type'
            syms.append({'kind': kind, 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
    return syms, imports


def extract_rust(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        if not s:
            continue
        m = re.match(r'^(?:pub(?:\([^)]*\))?\s+)?use\s+([A-Za-z_][\w:]*)\b', s)
        if m:
            top = m.group(1).split(':')[0]
            imports.append(top)
            syms.append({'kind': 'import', 'name': top, 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:pub(?:\([^)]*\))?\s+)?(?:async\s+|unsafe\s+|extern\s+"[^"]*"\s+)*fn\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': 'fn', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:pub(?:\([^)]*\))?\s+)?(struct|enum|trait|mod)\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:pub(?:\([^)]*\))?\s+)?impl\s+(.*)$', s)
        if m:
            rest = re.sub(r'<[^;]*>', ' ', m.group(1))
            name = rest.strip()
            fm = re.search(r'\bfor\s+([A-Za-z_]\w*)', rest)
            if fm:
                name = fm.group(1)
            else:
                nm = re.match(r'([A-Za-z_]\w*)', rest.strip())
                if nm:
                    name = nm.group(1)
            syms.append({'kind': 'impl', 'name': name, 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:pub(?:\([^)]*\))?\s+)?(const|static)\s+(?:mut\s+)?([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
    return syms, imports


def extract_java(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        if not s:
            continue
        m = re.match(r'^import\s+(?:static\s+)?([A-Za-z_]\w*)', s)
        if m:
            top = m.group(1)
            imports.append(top)
            syms.append({'kind': 'import', 'name': top, 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.search(r'\b(class|interface|enum|record)\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        if re.match(r'^(public|private|protected)\b', s) and \
                re.search(r'\w+\s*\([^;]*$', s):
            nm = re.search(r'([A-Za-z_]\w*)\s*\(', s)
            if nm:
                syms.append({'kind': 'method', 'name': nm.group(1), 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
    return syms, imports


def extract_kotlin(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        if not s:
            continue
        m = re.match(r'^import\s+([A-Za-z_]\w*)', s)
        if m:
            top = m.group(1)
            imports.append(top)
            syms.append({'kind': 'import', 'name': top, 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.search(r'\benum\s+class\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': 'enum', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.search(r'\b(class|interface|object)\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:(?:public|private|protected|internal)\s+)*(?:override\s+)?(?:suspend\s+)?fun\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': 'fun', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
    return syms, imports


def is_c_fn(s):
    if re.match(r'^[A-Za-z_][\w\s\*&:<>,]*\b\w+\s*\([^;]*$', s) and \
            re.search(r'\w+\s*\(', s):
        return True
    return s.endswith(') {')


def extract_c(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        if not s:
            continue
        if s.startswith('#'):
            # include specifiers are quoted/angled; read them from raw
            m = re.match(r'^#\s*include\s*[<"]([^>"]+)[>"]', raw)
            if m:
                mod = m.group(1).split('/')[-1]
                imports.append(mod)
                syms.append({'kind': 'import', 'name': mod, 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
                continue
            m = re.match(r'^#\s*define\s+([A-Za-z_]\w*)', raw)
            if m:
                syms.append({'kind': 'macro', 'name': m.group(1), 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
                continue
        if s.startswith('typedef'):
            m = re.match(r'^typedef\s+(struct|class|enum|union)\s+([A-Za-z_]\w*)', s)
            if m:
                syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
                continue
            nm = re.search(r'\b([A-Za-z_]\w*)\s*;', s)
            if nm:
                syms.append({'kind': 'typedef', 'name': nm.group(1), 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:typedef\s+)?(struct|class|enum|union)\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        if d == 0 and is_c_fn(s):
            nm = re.search(r'\b([A-Za-z_]\w*)\s*\(', s)
            name = nm.group(1) if nm else ''
            if name and name not in C_KEYWORDS:
                syms.append({'kind': 'fn?', 'name': name, 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
    return syms, imports


def extract_ruby(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        if not s:
            continue
        if s.startswith('require'):
            m = re.match(r'^require(?:_relative)?\s*\(?\s*["\']([^"\']+)["\']', raw)
            if m:
                mod = m.group(1)
                imports.append(mod)
                syms.append({'kind': 'import', 'name': mod, 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(class|module)\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^def\s+(?:self\.)?([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': 'def', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
    return syms, imports


def extract_php(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        if not s:
            continue
        if re.match(r'^use\s+(?:function|const)\s+', s):
            continue
        m = re.match(r'^use\s+([A-Za-z_]\w*)', s)
        if m:
            top = m.group(1)
            imports.append(top)
            syms.append({'kind': 'import', 'name': top, 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:abstract\s+|final\s+)?(class|interface|trait)\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:(?:public|private|protected)\s+)?(?:static\s+)?function\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': 'function', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
    return syms, imports


def extract_swift(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        if not s:
            continue
        if re.match(r'^import\s+(?:class|struct|enum|protocol|func|var|let|typealias)\s+', s):
            continue
        m = re.match(r'^import\s+(?:@testable\s+)?([A-Za-z_]\w*)', s)
        if m:
            top = m.group(1)
            imports.append(top)
            syms.append({'kind': 'import', 'name': top, 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:public|private|internal|fileprivate|open)?\s*(?:final\s+)?(class|struct|enum|protocol|extension)\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:public|private|internal|fileprivate|open)?\s*(?:static\s+|class\s+)?func\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': 'func', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        if d == 0:
            m = re.match(r'^(?:public|private|internal|fileprivate|open)?\s*(?:static\s+)?(var|let)\s+([A-Za-z_]\w*)', s)
            if m:
                syms.append({'kind': m.group(1), 'name': m.group(2), 'line': idx,
                             'signature': clean_sig(code), 'indent': d})
    return syms, imports


def extract_shell(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, (raw, code) in enumerate(zip(raw_lines, code_lines)):
        idx = i + 1
        d = depths[i]
        s = code.strip()
        if not s:
            continue
        m = re.match(r'^([A-Za-z_]\w*)\s*\(\s*\)\s*\{', s)
        if m:
            syms.append({'kind': 'function', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^function\s+([A-Za-z_]\w*)', s)
        if m:
            syms.append({'kind': 'function', 'name': m.group(1), 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
            continue
        m = re.match(r'^(?:source|\.)\s+([^\s;]+)', s)
        if m:
            mod = m.group(1)
            imports.append(mod)
            syms.append({'kind': 'import', 'name': mod, 'line': idx,
                         'signature': clean_sig(code), 'indent': d})
    return syms, imports


def extract_markdown(raw_lines, code_lines, depths):
    syms = []
    imports = []
    for i, raw in enumerate(raw_lines, 1):
        s = raw.rstrip()
        m = re.match(r'^(#{1,6})\s+(.*)$', s)
        if m:
            syms.append({'kind': 'heading', 'name': m.group(2).strip(),
                         'line': i, 'signature': clean_sig(s),
                         'level': len(m.group(1))})
    return syms, imports


EXTRACTORS = {
    'python': extract_python,
    'javascript': extract_jsts,
    'typescript': extract_jsts,
    'go': extract_go,
    'rust': extract_rust,
    'java': extract_java,
    'kotlin': extract_kotlin,
    'c': extract_c,
    'cpp': extract_c,
    'ruby': extract_ruby,
    'php': extract_php,
    'swift': extract_swift,
    'shell': extract_shell,
    'markdown': extract_markdown,
}

INDENT_LANGS = ('python', 'ruby', 'shell')


# --------------------------------------------------------------------------
# Nesting (parent assignment) and tree linking
# --------------------------------------------------------------------------


def assign_parents(symbols, containers):
    """Attach each symbol to the innermost open container, by nesting depth."""
    stack = []
    for sym in symbols:
        ind = sym.get('indent', 0)
        while stack and ind <= stack[-1][0]:
            stack.pop()
        if stack:
            sym['parent'] = stack[-1][1]
        else:
            sym['parent'] = None
        if sym['kind'] in containers:
            stack.append((ind, sym))
    return symbols


def assign_heading_parents(symbols):
    """Markdown headings nest by level: h2 belongs to the last open h1."""
    stack = []
    for sym in symbols:
        level = sym.get('level', 1)
        while stack and stack[-1][0] >= level:
            stack.pop()
        if stack:
            sym['parent'] = stack[-1][1]
        else:
            sym['parent'] = None
        stack.append((level, sym))
    return symbols


def link_children(symbols):
    for sym in symbols:
        sym['children'] = []
    for sym in symbols:
        p = sym.get('parent')
        if p is not None:
            p['children'].append(sym)


def extract_symbols(text, lang):
    raw_lines, code_lines, depths = analyze_lines(text, lang)
    fn = EXTRACTORS[lang]
    syms, imports = fn(raw_lines, code_lines, depths)
    if lang == 'markdown':
        assign_heading_parents(syms)
    else:
        assign_parents(syms, CONTAINERS.get(lang, set()))
    link_children(syms)
    return syms, imports


# --------------------------------------------------------------------------
# Discovery and per-file inspection
# --------------------------------------------------------------------------


def walk(root, excludes):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        keep = []
        for d in sorted(dirnames):
            if d.startswith('.') or d in SKIP_DIRS:
                continue
            rel_dir = os.path.relpath(os.path.join(dirpath, d), root)
            if any(fnmatch.fnmatch(rel_dir, pat) for pat in excludes):
                continue
            keep.append(d)
        dirnames[:] = keep
        for fn in sorted(filenames):
            if fn.startswith('.'):
                continue
            absf = os.path.join(dirpath, fn)
            relf = os.path.relpath(absf, root)
            if any(fnmatch.fnmatch(relf, pat) for pat in excludes):
                continue
            out.append((relf, absf))
    out.sort(key=lambda t: t[0])
    return out


def inspect_file(abs_path):
    info = {'path': abs_path, 'language': lang_for(abs_path),
            'tokens_est': None, 'lines': None, 'symbols': [], 'imports': [],
            'binary': False, 'unreadable': False, 'oversize': False,
            'unsupported': False, 'error': None}
    try:
        size = os.path.getsize(abs_path)
    except OSError as exc:
        info.update(unreadable=True, error=type(exc).__name__)
        return info
    info['tokens_est'] = int(size / 4 * 1.05)
    try:
        with open(abs_path, 'rb') as f:
            head = f.read(8192)
    except OSError as exc:
        info.update(unreadable=True, error=type(exc).__name__,
                    tokens_est=None)
        return info
    if b'\x00' in head:
        info['binary'] = True
        info['tokens_est'] = None
        return info
    try:
        info['lines'] = count_lines(abs_path)
    except OSError as exc:
        info.update(unreadable=True, error=type(exc).__name__,
                    tokens_est=None)
        return info
    if info['language'] is None:
        info['unsupported'] = True
        return info
    if size > MB_THRESHOLD:
        info['oversize'] = True
        return info
    try:
        with open(abs_path, 'rb') as f:
            data = f.read()
        text = data.decode('utf-8', errors='replace')
        info['symbols'], info['imports'] = extract_symbols(text, info['language'])
    except Exception as exc:
        info['error'] = type(exc).__name__
        info['symbols'] = []
        info['imports'] = []
    return info


def discover(root, excludes):
    entries = []
    if os.path.isdir(root):
        for rel, absf in walk(root, excludes):
            info = inspect_file(absf)
            info['path'] = rel
            entries.append((root, info))
    else:
        info = inspect_file(root)
        info['path'] = root
        entries.append((root, info))
    return entries


def explicit_entry(root):
    return os.path.isfile(root)


# --------------------------------------------------------------------------
# Emission
# --------------------------------------------------------------------------


def display_sig(sym):
    if sym['kind'] in SIG_KINDS:
        return sym['signature']
    return '{} {}'.format(sym['kind'], sym['name'])


def emit_sym(sym, depth):
    print('{}  L{}'.format('  ' * (depth + 1) + display_sig(sym), sym['line']))
    for child in sym.get('children', []):
        emit_sym(child, depth + 1)


def emit_map(entries):
    for root, info in entries:
        explicit = explicit_entry(root)
        if not explicit and (info['unsupported'] or info['binary']
                             or info['unreadable']):
            continue
        p = info['path']
        try:
            if info['unreadable']:
                print('File: {}  (tokens: pending)  (error: {})'.format(
                    p, info['error']))
            elif info['binary']:
                print('File: {}  (tokens: pending)  (no map: binary file)'.format(p))
            elif info['unsupported']:
                print('File: {}  (no map: unsupported language)'.format(p))
            elif info['oversize']:
                print('File: {}  ({}, {} lines)  (no map: oversize, 1.0MB+)'.format(
                    p, fmt_tokens(info['tokens_est']), info['lines']))
            else:
                print('File: {}  ({}, {} lines)'.format(
                    p, fmt_tokens(info['tokens_est']), info['lines']))
                if info['imports']:
                    print('  import: {}'.format(', '.join(dedup_cap(info['imports']))))
                for sym in info['symbols']:
                    if sym.get('parent') is None and sym['kind'] != 'import':
                        emit_sym(sym, 0)
        except Exception as exc:
            print('File: {}  (error: {})'.format(p, type(exc).__name__))


def tree_node_sort(children):
    return sorted(children,
                  key=lambda c: (0 if c['is_dir'] else 1, c['name'].lower()))


def build_tree(infos):
    root_node = {'name': '', 'children': {}, 'info': None, 'is_dir': True}
    for info in infos:
        parts = info['path'].split('/')
        node = root_node
        for part in parts[:-1]:
            node = node['children'].setdefault(
                part, {'name': part, 'children': {}, 'info': None,
                       'is_dir': True})
        node['children'][parts[-1]] = {
            'name': parts[-1], 'children': {}, 'info': info, 'is_dir': False}
    return root_node


def print_tree_node(node, depth, counters):
    prefix = '  ' * depth
    if node['is_dir']:
        print('{}{}/'.format(prefix, node['name']))
    else:
        info = node['info']
        if info['binary'] or info['unreadable']:
            suffix = 'tokens: pending'
        else:
            suffix = '{}, {} lines'.format(fmt_tokens(info['tokens_est']),
                                           info['lines'])
        print('{}{}  {}'.format(prefix, node['name'], suffix))
        counters['files'] += 1
        if info['tokens_est'] is not None:
            counters['tokens'] += info['tokens_est']
        else:
            counters['pending'] += 1
    for child in tree_node_sort(node['children'].values()):
        print_tree_node(child, depth + 1, counters)


def emit_tree(entries):
    counters = {'files': 0, 'tokens': 0, 'pending': 0}
    by_root = {}
    for root, info in entries:
        by_root.setdefault(root, []).append(info)
    for root in by_root:
        infos = by_root[root]
        if explicit_entry(root):
            info = infos[0]
            if info['binary'] or info['unreadable']:
                suffix = 'tokens: pending'
            else:
                suffix = '{}, {} lines'.format(fmt_tokens(info['tokens_est']),
                                               info['lines'])
            print('{}  {}'.format(info['path'], suffix))
            counters['files'] += 1
            if info['tokens_est'] is not None:
                counters['tokens'] += info['tokens_est']
            else:
                counters['pending'] += 1
        else:
            print('{}/'.format(os.path.basename(os.path.normpath(root))))
            node = build_tree(infos)
            for child in tree_node_sort(node['children'].values()):
                print_tree_node(child, 1, counters)
    total = 'TOTAL: {} files, {}'.format(counters['files'],
                                         fmt_tokens(counters['tokens']))
    if counters['pending']:
        total += ' + {} pending'.format(counters['pending'])
    print(total)


def clean_symbol(sym):
    return {'kind': sym['kind'], 'name': sym['name'], 'line': sym['line'],
            'signature': sym['signature']}


def emit_json(entries):
    files = []
    total = 0
    for root, info in entries:
        explicit = explicit_entry(root)
        if not explicit and (info['unsupported'] or info['binary']
                             or info['unreadable']):
            continue
        if info['unreadable'] or info['binary'] or info['unsupported']:
            lang = None
            syms = []
        elif info['oversize']:
            lang = info['language']
            syms = []
        else:
            lang = info['language']
            syms = [clean_symbol(s) for s in info['symbols']]
        files.append({'path': info['path'], 'tokens_est': info['tokens_est'],
                      'lines': info['lines'], 'language': lang,
                      'symbols': syms})
        if info['tokens_est'] is not None:
            total += info['tokens_est']
    print(json.dumps({'files': files, 'total_tokens_est': total}, indent=2))


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

USAGE = ('usage: python3 codemap.py PATH [PATH...] [--tree] [--json] '
         '[--exclude PAT ...]')


def parse_args(argv):
    paths = []
    excludes = []
    tree = False
    json_mode = False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--tree':
            tree = True
        elif a == '--json':
            json_mode = True
        elif a == '--exclude':
            i += 1
            while i < len(argv) and not argv[i].startswith('-'):
                # Stop at the first token that names an existing path so a
                # PATH may legally follow --exclude PAT ... in any order.
                if os.path.exists(argv[i]):
                    break
                excludes.append(argv[i])
                i += 1
            continue
        elif a.startswith('-'):
            sys.stderr.write('codemap: unknown option: {}\n'.format(a))
            return None, None, None, None, 2
        else:
            paths.append(a)
        i += 1
    return paths, excludes, tree, json_mode, None


def main(argv):
    parsed = parse_args(argv)
    paths, excludes, tree, json_mode, err = parsed
    if err is not None:
        sys.stderr.write(USAGE + '\n')
        return err
    if not paths:
        sys.stderr.write(USAGE + '\n')
        return 2
    for p in paths:
        if not os.path.exists(p):
            sys.stderr.write('codemap: no such path: {}\n'.format(p))
            return 2
    entries = []
    for p in paths:
        entries.extend(discover(p, excludes))
    if json_mode:
        emit_json(entries)
    elif tree:
        emit_tree(entries)
    else:
        emit_map(entries)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
