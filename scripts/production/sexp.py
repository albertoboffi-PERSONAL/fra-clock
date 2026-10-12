import re
TOK = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')
def parse(s):
    stack = [[]]; pos = 0; n = len(s)
    while pos < n:
        m = TOK.match(s, pos)
        if not m:
            if s[pos:].strip() == "": break
            raise ValueError(pos)
        pos = m.end()
        if m.group(1): stack.append([])
        elif m.group(2):
            t = stack.pop(); stack[-1].append(t)
        elif m.group(3) is not None: stack[-1].append(m.group(3).replace('\\"', '"'))
        elif m.group(4) is not None: stack[-1].append(m.group(4))
    return stack[0][0]
def find(node, key): return [c for c in node if isinstance(c, list) and c and c[0] == key]
def first(node, key):
    r = find(node, key); return r[0] if r else None
