import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument(
    "report",
    help="Path to report file in markdown format",
    type=argparse.FileType("r+", encoding="UTF-8"),
)


def remove_plan(report: str) -> str:
    report_lines = [
        f"### ⚠️ _Terraform plan details have been removed from the report to fit within the maximum comment length. Check [workflow summary]({os.environ("GITHUB_SERVER_URL")}/{os.environ("GITHUB_REPOSITORY")}/actions/runs/{os.environ("GITHUB_RUN_ID")}) for the full report._",
        "",
        "---",
        ""
    ]
    add_line = True
    for line in report.splitlines():
        if add_line and line == "<details><summary>Show Plan</summary>":
            add_line = False
        if add_line:
            report_lines.append(line)
        if not add_line and line == "</details>":
            add_line = True
    return "\n".join(report_lines)


if __name__ == "__main__":
    args = parser.parse_args()

    report = args.report.read()
    if len(report) > 65536:
        report = remove_plan(report)

    args.report.seek(0)
    args.report.truncate()
    args.report.write(report)
