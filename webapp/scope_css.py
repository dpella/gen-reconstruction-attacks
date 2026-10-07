"""
Turn the stand-alone site's stylesheet into one scoped under `.recon` for
the page on dpella.io:
- prefix every selector;
- rename our custom properties to --rc-*, because DPella's site defines
  --muted, --accent and --border with other meanings;
- map colours to DPella's theme variables;
- drop the page chrome (header, footer, system dark mode) that DPella's
  site provides itself.

    python3 webapp/scope_css.py webapp/frontend/src/styles.css \
        ../dpella-web-lovable/src/components/reconstruction/reconstruction.css
"""
import re
import sys

src, dst = sys.argv[1], sys.argv[2]
css = open(src).read()

# Our tokens -> --rc-*; DPella defines --muted/--accent/--border differently.
TOKENS = ["bg", "surface-2", "surface", "text", "muted", "border", "accent-soft", "accent-text",
          "accent", "green", "blue", "navy", "secret-soft", "secret", "ok", "cell-off", "flip", "radius"]
for t in TOKENS:
    css = re.sub(rf"var\(--{t}\)", f"var(--rc-{t})", css)

# Rules that belong to the stand-alone page chrome (DPella provides its own).
DROP = re.compile(r"^(:root|\*|body|\.wrap|\.topbar|\.topbar-inner|\.brand|\.brand picture|\.brand-logo|"
                  r"\.brand-name|\.footer|\.footer \.wrap|\.footer-logo|\.footer picture)$")


def blocks(text):
    """Yield (prelude, body) for each top-level block, skipping comments."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    i = 0
    while True:
        j = text.find("{", i)
        if j == -1:
            return
        depth, k = 1, j + 1
        while depth:
            depth += {"{": 1, "}": -1}.get(text[k], 0)
            k += 1
        yield text[i:j].strip(), text[j + 1:k - 1]
        i = k


def scope_rules(text):
    out = []
    for prelude, body in blocks(text):
        if prelude.startswith("@keyframes"):
            out.append(f"{prelude.replace('flow', 'rc-flow')} {{{body}}}")
            continue
        if prelude.startswith("@media"):
            if "prefers-color-scheme" in prelude:
                continue  # DPella's site has no system dark mode
            inner = scope_rules(body)
            if inner.strip():
                out.append(f"{prelude} {{\n{inner}\n}}")
            continue
        sels = [s.strip() for s in prelude.split(",")]
        if all(DROP.match(s) for s in sels):
            continue
        keep = [s for s in sels if not DROP.match(s)]
        scoped = ", ".join(f".recon {s}" for s in keep)
        body = body.replace("animation: flow", "animation: rc-flow")
        out.append(f"{scoped} {{{body}}}")
    return "\n".join(out)


header = """/*
 * Styles for the EHDS & Privacy Risks page, scoped under `.recon`.
 * Generated from github.com/dpella/gen-reconstruction-attacks
 * (webapp/frontend/src/styles.css); colours come from DPella's theme.
 */
.recon {
  --rc-bg: hsl(var(--background));
  --rc-surface: hsl(var(--card));
  --rc-surface-2: hsl(var(--muted));
  --rc-text: hsl(var(--foreground));
  --rc-muted: hsl(var(--muted-foreground));
  --rc-border: hsl(var(--border));
  --rc-accent: hsl(var(--primary));
  --rc-accent-soft: hsl(var(--primary) / 0.12);
  --rc-accent-text: hsl(var(--primary-foreground));
  --rc-green: hsl(var(--secondary));
  --rc-blue: hsl(var(--accent));
  --rc-navy: hsl(var(--foreground));
  --rc-secret: hsl(var(--destructive));
  --rc-secret-soft: hsl(var(--destructive) / 0.08);
  --rc-ok: hsl(152 45% 36%);
  --rc-cell-off: hsl(var(--muted));
  --rc-flip: hsl(var(--accent));
  --rc-radius: var(--radius);
  color: var(--rc-text);
}
/* Tailwind's reset removes spacing and list markers the page relies on. */
.recon p { margin: 1em 0; }
.recon ul.bullets { list-style: disc; padding-left: 1.2rem; }
.recon h1, .recon h2, .recon h3 { font-weight: 700; }
.recon a { text-decoration: underline; text-underline-offset: 2px; }
"""
open(dst, "w").write(header + scope_rules(css) + "\n")
print("rules:", scope_rules(css).count("{"))
