import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "report",
    help="Path to report file in markdown format",
    type=argparse.FileType("r+", encoding="UTF-8"),
)


def remove_plan(report: str) -> str:
    report_lines = []
    add_line = True
    for line in report.splitlines():
        if add_line and line == "<details><summary>Show Plan</summary>":
            add_line = False
        if add_line:
            report_lines.append(line)
        if not add_line and line == "</details>":
            add_line = True

    report_lines.append("")
    eport_lines.append("---")
    eport_lines.append("")
    eport_lines.append("Note: the terraform plans are too long. Please check the workflow summary to view the full report.")
    return "\n".join(report_lines)


if __name__ == "__main__":
    args = parser.parse_args()

    report = args.report.read()
    if len(report) > 65536:
        report = remove_plan(report)

    args.report.seek(0)
    args.report.truncate()
    args.report.write(report)
