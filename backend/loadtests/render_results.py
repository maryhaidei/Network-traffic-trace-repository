import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
INPUT_CSV = RESULTS_DIR / "summary_mean_by_users.csv"

OUT_TXT = RESULTS_DIR / "summary_mean_by_users.txt"
OUT_MD = RESULTS_DIR / "summary_mean_by_users.md"
OUT_TEX = RESULTS_DIR / "summary_mean_by_users.tex"


COLUMNS = [
    ("users", "Пользователи"),
    ("runs", "Прогоны"),
    ("failed_runs", "Сбойные прогоны"),
    ("error_rate_pct_mean", "Доля ошибочных запросов, %"),
    ("avg_response_time_ms_mean", "Среднее время ответа, мс"),
    ("p95_response_time_ms_mean", "95-й перцентиль, мс"),
    ("throughput_rps_mean", "Пропускная способность, запросов/с"),
    ("processed_requests_mean", "Число обработанных запросов"),
]


def read_csv_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def format_number(value: str) -> str:
    if value is None or value == "":
        return "-"
    try:
        num = float(value)
    except ValueError:
        return value

    if abs(num - round(num)) < 1e-9:
        return str(int(round(num)))
    return f"{num:.2f}"


def normalize_rows(rows: list[dict]) -> list[list[str]]:
    table = []
    for row in rows:
        formatted = []
        for key, _title in COLUMNS:
            formatted.append(format_number(row.get(key, "")))
        table.append(formatted)
    return table


def build_text_table(rows: list[list[str]]) -> str:
    headers = [title for _key, title in COLUMNS]
    widths = [len(h) for h in headers]

    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def fmt_row(items):
        return " | ".join(item.ljust(widths[i]) for i, item in enumerate(items))

    sep = "-+-".join("-" * w for w in widths)

    lines = [fmt_row(headers), sep]
    for row in rows:
        lines.append(fmt_row(row))

    return "\n".join(lines)


def build_markdown_table(rows: list[list[str]]) -> str:
    headers = [title for _key, title in COLUMNS]
    align = ["---"] * len(headers)

    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(align) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def build_latex_table(rows: list[list[str]]) -> str:
    headers = [title for _key, title in COLUMNS]

    col_spec = " | ".join(["c"] * len(headers))
    lines = []
    lines.append("\\begin{table}[h!]")
    lines.append("\\centering")
    lines.append("\\caption{Средние результаты нагрузочного тестирования}")
    lines.append("\\label{tab:loadtest_mean_results}")
    lines.append(f"\\begin{{tabular}}{{|{col_spec}|}}")
    lines.append("\\hline")
    lines.append(" & ".join(headers) + " \\\\")
    lines.append("\\hline")

    for row in rows:
        escaped = [cell.replace("%", "\\%") for cell in row]
        lines.append(" & ".join(escaped) + " \\\\")
        lines.append("\\hline")

    lines.append("\\end{tabular}")
    lines.append("\\end{table}")
    return "\n".join(lines)


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Не найден файл: {INPUT_CSV}")

    raw_rows = read_csv_rows(INPUT_CSV)
    rows = normalize_rows(raw_rows)

    text_table = build_text_table(rows)
    markdown_table = build_markdown_table(rows)
    latex_table = build_latex_table(rows)

    OUT_TXT.write_text(text_table, encoding="utf-8")
    OUT_MD.write_text(markdown_table, encoding="utf-8")
    OUT_TEX.write_text(latex_table, encoding="utf-8")

    print("Таблица результатов:\n")
    print(text_table)
    print(f"\nСохранено в:\n- {OUT_TXT}\n- {OUT_MD}\n- {OUT_TEX}")


if __name__ == "__main__":
    main()
