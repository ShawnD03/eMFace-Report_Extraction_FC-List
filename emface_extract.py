import argparse
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json


@dataclass
class TkRow:
    fc: str
    version: str
    revision: str
    is_sum_config: bool
    group_index: int


def read_text_with_fallback(file_path: Path) -> str:
    data = file_path.read_bytes()
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("latin-1", errors="replace")


def extract_general_info(text: str) -> dict:
    program_version = "Not found"
    pver_version = "Not found"
    date_value = "Not found"
    sum_config = "Not found"

    program_match = re.search(r"Program\s*:\s*EMFace\s+(v\S+)", text)
    if program_match:
        program_version = program_match.group(1).strip()

    pver_match = re.search(r"PVER\s+version\s*:\s*(.+)", text)
    if pver_match:
        pver_version = pver_match.group(1).strip()

    date_match = re.search(r"Date\s*:\s*([A-Za-z]{3}\s+[A-Za-z]{3}\s+\d{2})\s+\d{2}:\d{2}:\d{2}\s+\w+\s+(\d{4})", text)
    if date_match:
        raw_date = f"{date_match.group(1)} {date_match.group(2)}"
        try:
            date_value = datetime.strptime(raw_date, "%a %b %d %Y").strftime("%d.%m.%Y")
        except ValueError:
            date_value = raw_date
    else:
        raw_date_match = re.search(r"Date\s*:\s*(.+)", text)
        if raw_date_match:
            raw_date = raw_date_match.group(1).strip()
            raw_date = re.sub(r"\s+\d{2}:\d{2}:\d{2}.*", "", raw_date).strip()
            try:
                date_value = datetime.strptime(raw_date, "%a %b %d %Y").strftime("%d.%m.%Y")
            except ValueError:
                date_value = raw_date

    sum_match = re.search(r"Summenkonfiguration\s*:\s*(.+)", text)
    if sum_match:
        sum_config = sum_match.group(1).strip()

    return {
        "program_version": program_version,
        "pver_version": pver_version,
        "date": date_value,
        "sum_config": sum_config,
    }


def normalize_revision(revision: str) -> str:
    return re.sub(r"[^0-9]", "", revision)


def parse_fc_value(value: str) -> Optional[tuple]:
    value = value.strip()
    if value.lower() == "--missing--":
        return "--missing--", "--missing--", ""

    match_full = re.match(r"(.+?)\s*/\s*([^;]+);\s*([^\s]+)", value)
    if match_full:
        fc = match_full.group(1).strip()
        version = match_full.group(2).strip()
        revision = normalize_revision(match_full.group(3).strip())
        return fc, version, revision

    match_missing_version = re.match(r"(.+?)\s*/\s*;\s*([^\s]+)", value)
    if match_missing_version:
        fc = match_missing_version.group(1).strip()
        revision = normalize_revision(match_missing_version.group(2).strip())
        return fc, "--.--.--", revision

    match_version_no_rev = re.match(r"(.+?)\s*/\s*([^\s]+)", value)
    if match_version_no_rev:
        fc = match_version_no_rev.group(1).strip()
        version = match_version_no_rev.group(2).strip()
        return fc, version, ""

    if value:
        return value, "--.--.--", ""

    return None


def extract_tk_rows(text: str) -> List[TkRow]:
    lines = text.splitlines()
    section_index = None
    for idx, line in enumerate(lines):
        if "Comparison of Variants and Revisions for FC data" in line:
            section_index = idx
            break

    if section_index is None:
        return []

    fc_rows = []
    group_index = -1
    last_fc = None

    for line in lines[section_index + 1 :]:
        if "Summenkonfiguration FC" in line or "Element in PVER FC" in line:
            kind_match = re.search(
                r"(Summenkonfiguration FC(?:-ARB)?|Element in PVER FC(?:-ARB)?)\s*:\s*(.+)",
                line,
            )
            if not kind_match:
                continue
            kind = kind_match.group(1)
            value = kind_match.group(2)
            parsed = parse_fc_value(value)
            if parsed is None:
                continue
            fc, version, revision = parsed
            is_element = kind.startswith("Element in PVER FC")
            if fc != last_fc:
                group_index += 1
                last_fc = fc
            fc_rows.append(TkRow(fc, version, revision, is_element, group_index))

    return fc_rows


def generate_html(general_info: dict, tk_rows: List[TkRow]) -> str:
    html = f"""
    <html>
    <head>
        <title>EMFace Extract</title>
        <style>
            :root {{
                --bg: #f7f9fc;
                --card: #ffffff;
                --text: #111827;
                --muted: #6b7280;
                --border: #e5e7eb;
                --accent: #2563eb;
                --row-alt: #e8f2ff;
            }}
            body {{
                margin: 0;
                font-family: "Segoe UI", Arial, sans-serif;
                background: var(--bg);
                color: var(--text);
            }}
            .container {{
                max-width: 1100px;
                margin: 28px auto;
                padding: 0 18px 36px;
            }}
            h1 {{
                margin: 0 0 8px;
                font-size: 24px;
            }}
            h2 {{
                margin: 24px 0 12px;
                font-size: 18px;
            }}
            .card {{
                background: var(--card);
                border: 1px solid var(--border);
                border-radius: 10px;
                padding: 14px 16px;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th, td {{
                text-align: left;
                padding: 8px 10px;
                border-bottom: 1px solid var(--border);
                vertical-align: top;
            }}
            th {{
                background: #f3f4f6;
                font-weight: 600;
            }}
            .row-alt {{
                background: var(--row-alt);
            }}
            .muted {{
                color: var(--muted);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>EMFace Extract</h1>

            <h2>Allgemeine Informationen</h2>
            <div class="card">
                <table>
                    <tbody>
                        <tr><th>eMFace-Version</th><td>{general_info['program_version']}</td></tr>
                        <tr><th>PVER Version</th><td>{general_info['pver_version']}</td></tr>
                        <tr><th>Datum</th><td>{general_info['date']}</td></tr>
                        <tr><th>Summenkonfiguration</th><td>{general_info['sum_config']}</td></tr>
                    </tbody>
                </table>
            </div>

            <h2>TK-Informationen</h2>
            <div class="card">
                <table>
                    <thead>
                        <tr>
                            <th>FC</th>
                            <th>Version</th>
                            <th>Revision</th>
                        </tr>
                    </thead>
                    <tbody>
    """

    for row in tk_rows:
        row_class = "row-alt" if row.group_index % 2 == 1 else ""
        fc_display = f"<b>{row.fc}</b>" if row.is_sum_config else row.fc
        html += (
            f"<tr class=\"{row_class}\">"
            f"<td>{fc_display}</td>"
            f"<td>{row.version}</td>"
            f"<td>{row.revision}</td>"
            "</tr>"
        )

    html += """
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def run(input_file: Path, output_file: Optional[Path] = None) -> Path:
    text = read_text_with_fallback(input_file)
    general_info = extract_general_info(text)
    tk_rows = extract_tk_rows(text)

    if output_file is None:
        output_file = input_file.with_suffix(".html")

    html = generate_html(general_info, tk_rows)
    output_file.write_text(html, encoding="utf-8")
    json_file = output_file.with_suffix(".json")
    json_rows = [
        {
            "fc": row.fc,
            "version": row.version,
            "revision": row.revision,
            "source": "Element in PVER FC" if row.is_sum_config else "Summenkonfiguration FC",
        }
        for row in tk_rows
        if row.version and row.version not in {"--missing--", "--.--.--"}
    ]
    json_payload = {"general": general_info, "tk_info": json_rows, "Mail": "daniel.damm@de.bosch.com"}
    json_file.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract EMFace report data to HTML.")
    parser.add_argument("input_file", help="Pfad zur EMFace-Report-Textdatei")
    parser.add_argument("-o", "--output", help="Pfad zur Ausgabe-HTML-Datei")
    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        raise SystemExit(f"Datei nicht gefunden: {input_path}")

    output_path = Path(args.output) if args.output else None
    result_path = run(input_path, output_path)
    print(f"HTML erstellt: {result_path}")


if __name__ == "__main__":
    main()
