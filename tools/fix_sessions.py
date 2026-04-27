import pathlib
import re

root = pathlib.Path('..').resolve() if pathlib.Path('.').name == 'tools' else pathlib.Path('.')
print(f'root={root}')

re_assign = re.compile(r'^(\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*SessionLocal\(\)\s*$')

for path in sorted(root.rglob('*.py')):
    if path.name == 'fix_sessions.py':
        continue

    text = path.read_text(encoding='utf-8')
    if 'SessionLocal()' not in text and 'with get_session() as' not in text:
        continue

    lines = text.splitlines()
    modified = False

    # import replacement
    new_lines = []
    for line in lines:
        if 'from database.db import SessionLocal' in line and 'get_session' not in line:
            line = line.replace('from database.db import SessionLocal', 'from database.db import SessionLocal, get_session')
            modified = True
        new_lines.append(line)
    lines = new_lines

    # replace direct SessionLocal assignments with context manager
    for i, line in enumerate(lines):
        m = re_assign.match(line)
        if m:
            indent = m.group(1)
            var = m.group(2)
            lines[i] = f'{indent}with get_session() as {var}:'
            modified = True

    # Basic try/finally cleanup inside with block
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('with get_session() as'):
            j = i + 1
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines) and lines[j].strip() == 'try:':
                del lines[j]
                with_indent = len(line) - len(line.lstrip(' '))
                body_indent = with_indent + 4
                k = j
                while k < len(lines):
                    if lines[k].strip() == '':
                        k += 1
                        continue
                    cur_indent = len(lines[k]) - len(lines[k].lstrip(' '))
                    if cur_indent >= body_indent:
                        lines[k] = lines[k][4:] if len(lines[k]) >= 4 else lines[k]
                        k += 1
                    else:
                        break
                if k < len(lines) and lines[k].strip() == 'finally:':
                    del lines[k]
                    if k < len(lines) and lines[k].strip() == '':
                        del lines[k]
                modified = True
                continue
        i += 1

    if modified:
        path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print('fixed', path)
