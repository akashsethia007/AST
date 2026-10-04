"""Strip all non-ASCII characters from Top200ST72.py so it runs on cp1252 systems."""
path = r'C:\Users\User\PycharmProjects\AST\Code\Top200ST72.py'

replacements = [
    ('\u2550', '='),    # ═  double horizontal
    ('\u2500', '-'),    # ─  single horizontal
    ('\u2192', '->'),   # →  arrow
    ('\u2014', '--'),   # —  em dash
    ('\u2013', '-'),    # –  en dash
    ('\u20b9', 'Rs.'),  # ₹  rupee
    ('\u00d7', 'x'),    # ×  multiply
    ('\u2502', '|'),    # │  vertical
    ('\u251c', '+'),    # ├
    ('\u2524', '+'),    # ┤
    ('\u252c', '+'),    # ┬
    ('\u2534', '+'),    # ┴
    ('\u253c', '+'),    # ┼
    ('\u2518', '+'),    # ┘
    ('\u250c', '+'),    # ┌
    ('\u2510', '+'),    # ┐
    ('\u2514', '+'),    # └
    ('\u2015', '--'),   # ― horizontal bar
    ('\u2012', '-'),    # ‒ figure dash
]

with open(path, encoding='utf-8') as f:
    content = f.read()

for old, new in replacements:
    content = content.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done. Any remaining non-ASCII:")
non_ascii = [(i+1, ch) for i, ch in enumerate(content) if ord(ch) > 127]
for lineno, ch in non_ascii[:20]:
    print(f"  pos {lineno}: {repr(ch)}")
if not non_ascii:
    print("  None found - file is clean ASCII.")
