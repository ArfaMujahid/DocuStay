"""
Convert a Markdown file to PDF with formatting and styling that matches the MD structure.
Uses only reportlab (no extra deps). Optional: pip install markdown xhtml2pdf for HTML path.
Usage: python scripts/md_to_pdf.py [input.md] [output.pdf]
Defaults: docs/PRODUCT_SYSTEM_OVERVIEW.md -> docs/PRODUCT_SYSTEM_OVERVIEW.pdf
"""
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

# Default paths
DEFAULT_INPUT = os.path.join(PROJECT_ROOT, "docs", "PRODUCT_SYSTEM_OVERVIEW.md")
DEFAULT_OUTPUT = os.path.join(PROJECT_ROOT, "docs", "PRODUCT_SYSTEM_OVERVIEW.pdf")


def try_xhtml2pdf(input_path: str, output_path: str) -> bool:
    """Use markdown + xhtml2pdf if available. Returns True if PDF was written."""
    try:
        import markdown
        from xhtml2pdf import pisa
    except ImportError:
        return False

    STYLE = """
    body { font-family: Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.45; color: #24292e; }
    h1 { font-size: 22pt; font-weight: bold; margin-top: 1.2em; margin-bottom: 0.5em; border-bottom: 1px solid #eaecef; }
    h2 { font-size: 16pt; font-weight: bold; margin-top: 1.2em; margin-bottom: 0.4em; }
    h3 { font-size: 13pt; font-weight: bold; margin-top: 1em; margin-bottom: 0.35em; }
    p { margin-top: 0.5em; margin-bottom: 0.5em; }
    hr { border: none; border-top: 1px solid #eaecef; margin: 1.5em 0; }
    ul, ol { margin: 0.5em 0; padding-left: 2em; }
    li { margin: 0.25em 0; }
    strong { font-weight: bold; }
    code { font-family: monospace; font-size: 10pt; background: #f6f8fa; padding: 0.15em 0.35em; }
    table { width: 100%; border-collapse: collapse; margin: 0.75em 0; font-size: 10.5pt; }
    th, td { border: 1px solid #dfe2e5; padding: 0.4em 0.6em; text-align: left; }
    th { font-weight: bold; background: #f6f8fa; }
    """
    with open(input_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    md = markdown.Markdown(extensions=["tables", "nl2br"])
    body_html = md.convert(md_text)
    html_doc = f"""<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml"><head><meta charset="UTF-8"/><style>{STYLE}</style></head><body>{body_html}</body></html>"""
    with open(output_path, "w+b") as out:
        status = pisa.CreatePDF(html_doc.encode("utf-8"), dest=out, encoding="utf-8")
        if status.err:
            return False
    return True


def escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def parse_inline(text: str) -> list:
    """Split text into (style_name, fragment) for ReportLab. Handles **bold** and `code`."""
    from reportlab.lib.enums import TA_LEFT

    frags = []
    rest = text
    while rest:
        m_b = re.match(r"^\*\*(.+?)\*\*", rest)
        m_c = re.match(r"^`([^`]+)`", rest)
        if m_b:
            frags.append(("bold", m_b.group(1)))
            rest = rest[m_b.end() :]
        elif m_c:
            frags.append(("code", m_c.group(1)))
            rest = rest[m_c.end() :]
        else:
            # take until next ** or `
            pos = len(rest)
            for sep in ["**", "`"]:
                i = rest.find(sep)
                if i != -1 and i < pos:
                    pos = i
            frags.append(("normal", rest[:pos]))
            rest = rest[pos:]
    return frags


def build_pdf_reportlab(input_path: str, output_path: str) -> None:
    """Build PDF with reportlab only: parse MD and render."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    body = styles["Normal"]
    body.fontSize = 11
    body.leading = 14
    h1 = styles["Heading1"]
    h1.fontSize = 22
    h1.spaceAfter = 12
    h2 = styles["Heading2"]
    h2.fontSize = 16
    h2.spaceAfter = 8
    h3 = styles["Heading3"]
    h3.fontSize = 13
    h3.spaceAfter = 6

    story = []
    i = 0
    while i < len(lines):
        line = lines[i]
        raw = line.rstrip("\n")
        stripped = raw.strip()

        if not stripped:
            story.append(Spacer(1, 8))
            i += 1
            continue

        if re.match(r"^# ", stripped):
            title = escape(stripped[2:].strip())
            story.append(Paragraph(title, h1))
            i += 1
            continue
        if re.match(r"^## ", stripped):
            title = escape(stripped[3:].strip())
            story.append(Paragraph(title, h2))
            i += 1
            continue
        if re.match(r"^### ", stripped):
            title = escape(stripped[4:].strip())
            story.append(Paragraph(title, h3))
            i += 1
            continue

        if re.match(r"^-{3,}\s*$", stripped):
            story.append(Spacer(1, 16))
            i += 1
            continue

        # Table: line starts with |
        if stripped.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].rstrip("\n"))
                i += 1
            if not table_lines:
                i += 1
                continue
            # Parse table: split by |, drop first/last empty
            rows = []
            for tl in table_lines:
                parts = tl.split("|")
                cells = [p.strip() for p in parts[1:-1]]
                rows.append(cells)
            if not rows:
                i += 1
                continue
            # Skip separator row (|---|---|)
            def cell_para(c):
                parts = re.split(r"\*\*(.+?)\*\*", c)
                out = []
                for j, p in enumerate(parts):
                    if j % 2 == 0:
                        out.append(escape(p))
                    else:
                        out.append("<b>" + escape(p) + "</b>")
                return Paragraph("".join(out), body)
            data = []
            for r in rows:
                if all(re.match(r"^:?-+:?$", c) for c in r):
                    continue
                data.append([cell_para(c) for c in r])
            if data:
                t = Table(data)
                t.setStyle(
                    TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f6f8fa")),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ]
                    )
                )
                story.append(t)
                story.append(Spacer(1, 10))
            continue

        # Unordered list
        if stripped.startswith("- ") or stripped.startswith("* "):
            text = stripped[2:].strip()
            frags = parse_inline(text)
            ptext = "".join(
                '<b><font face="Helvetica-Bold">' + escape(f[1]) + "</font></b>" if f[0] == "bold"
                else '<font face="Courier" backColor="#f0f0f0">' + escape(f[1]) + "</font>" if f[0] == "code"
                else escape(f[1])
                for f in frags
            )
            story.append(Paragraph("&#8226; " + ptext, body))
            i += 1
            continue

        # Ordered list (digit. )
        num_list = re.match(r"^(\d+)\.\s+", stripped)
        if num_list:
            text = stripped[num_list.end() :].strip()
            frags = parse_inline(text)
            ptext = "".join(
                '<b><font face="Helvetica-Bold">' + escape(f[1]) + "</font></b>" if f[0] == "bold"
                else '<font face="Courier" backColor="#f0f0f0">' + escape(f[1]) + "</font>" if f[0] == "code"
                else escape(f[1])
                for f in frags
            )
            story.append(Paragraph(num_list.group(1) + ". " + ptext, body))
            i += 1
            continue

        # Indented continuation (e.g. "   - sub")
        if raw.startswith("   ") and (raw.strip().startswith("- ") or raw.strip().startswith("* ")):
            text = raw.strip()[2:].strip()
            ptext = "".join(
                '<b><font face="Helvetica-Bold">' + escape(f[1]) + "</font></b>" if f[0] == "bold"
                else '<font face="Courier" backColor="#f0f0f0">' + escape(f[1]) + "</font>" if f[0] == "code"
                else escape(f[1])
                for f in parse_inline(text)
            )
            story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;&#8226; " + ptext, body))
            i += 1
            continue

        # Normal paragraph (may contain ** and `)
        frags = parse_inline(stripped)
        ptext = "".join(
            '<b><font face="Helvetica-Bold">' + escape(f[1]) + "</font></b>" if f[0] == "bold"
            else '<font face="Courier" backColor="#f0f0f0" size="10">' + escape(f[1]) + "</font>" if f[0] == "code"
            else escape(f[1])
            for f in frags
        )
        story.append(Paragraph(ptext, body))
        i += 1

    doc.build(story)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Convert Markdown to PDF")
    parser.add_argument("input", nargs="?", default=DEFAULT_INPUT, help="Input .md file")
    parser.add_argument("output", nargs="?", default=DEFAULT_OUTPUT, help="Output .pdf file")
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output)

    if not os.path.isfile(input_path):
        print(f"Error: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if try_xhtml2pdf(input_path, output_path):
        print(f"PDF written (xhtml2pdf): {output_path}")
        return

    try:
        build_pdf_reportlab(input_path, output_path)
        print(f"PDF written (reportlab): {output_path}")
    except Exception as e:
        print("Install optional deps for best formatting: pip install markdown xhtml2pdf", file=sys.stderr)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
