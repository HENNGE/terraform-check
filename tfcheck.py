import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

from jinja2 import Environment, FileSystemLoader

FMT_CMD = "terraform fmt -check=true -write=false -recursive -diff"
INIT_CMD = "terraform init -no-color"
VALIDATE_CMD = "terraform validate -no-color"
PLAN_CMD = "terraform plan -detailed-exitcode -no-color"

parser = argparse.ArgumentParser()
parser.add_argument("path", help="path to run terraform checks", type=str)
parser.add_argument(
    "-plan-args", help="addition args to pass to terraform plan", type=str
)
parser.add_argument(
    "-report",
    help="print report to a file, removing plans if report length > 65336",
    type=argparse.FileType("a", encoding="UTF-8"),
)
parser.add_argument(
    "-hide-refresh",
    help="hide terraform state refresh output from report",
    action=argparse.BooleanOptionalAction,
)
parser.add_argument(
    "-full-report",
    help="print full report to a file",
    type=argparse.FileType("a", encoding="UTF-8"),
)

env = Environment(loader=FileSystemLoader(f"{os.path.dirname(__file__)}/templates"))
template = env.get_template("tfcheck.md")


@dataclass
class CommandResult:
    output: str
    returncode: int


@dataclass
class CheckResult:
    path: str
    init_success: bool
    init_output: str
    fmt_success: bool
    fmt_output: str
    validate_success: bool
    validate_output: str
    plan_returncode: int
    plan_success: bool
    plan_changes: bool
    plan_output: str

    def exitcode(self) -> int:
        if self.fmt_success and self.validate_success:
            return self.plan_returncode
        else:
            return 1

    def check_result_msg(self) -> str:
        check_code = self.exitcode()
        if check_code == 0:
            return "✅Passed: there are no changes✅"
        elif check_code == 1:
            return "⛔️Failed: see details⛔️"
        else:
            return "⚠️There are changes: see details⚠"

    def init_result(self) -> str:
        return "success" if self.init_success else "failed"

    def fmt_result(self) -> str:
        return "success" if self.fmt_success else "failed"

    def validate_result(self) -> str:
        return "success" if self.validate_success else "failed"

    def plan_result(self) -> str:
        return "success" if self.plan_success else "failed"

    def plan_msg(self) -> str:
        if self.plan_returncode == 0:
            return "✅Passed: there are no changes✅"
        elif self.plan_returncode == 1:
            return "⛔️Failed: see details⛔️"
        else:
            return "⚠️There are changes: see details⚠️"


def run(cmd: str, path: str) -> subprocess.CompletedProcess:
    process = subprocess.run(
        cmd.split(),
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
    )
    print("-" * 77)
    print(f"{cmd} (path: {path})")
    print("-" * 77)
    print(process.stdout)
    return process


def check(path: str, plan_args: Optional[str] = None) -> CheckResult:
    # Terraform init
    init = run(INIT_CMD, path)

    # Terraform fmt
    fmt = run(FMT_CMD, path)

    # Terraform validate
    validate = run(VALIDATE_CMD, path)

    # Terraform plan
    if plan_args:
        plan = run(PLAN_CMD + " " + plan_args, path)
    else:
        plan = run(PLAN_CMD, path)

    return CheckResult(
        path=path,
        init_success=not init.returncode,
        init_output=init.stdout,
        fmt_success=not fmt.returncode,
        fmt_output=fmt.stdout,
        validate_success=not validate.returncode,
        validate_output=validate.stdout,
        # Terraform plan return code 2 = Succeeded with non-empty diff (changes present)
        plan_returncode=plan.returncode,
        plan_success=plan.returncode in [0, 2],
        plan_changes=plan.returncode == 2,
        plan_output=plan.stdout,
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
    return "\n".join(report_lines)


if __name__ == "__main__":
    args = parser.parse_args()

    result = check(args.path, args.plan_args)
    print(f"Terraform check on {args.path} {result.check_result_msg()}")

    # Remove refreshing messages from plan output
    if args.hide_refresh:
        result.plan_output = "\n".join(
            line
            for line in result.plan_output.split("\n")
            if not any(
                pattern in line
                for pattern in (
                    "Refreshing state...",
                    "Reading...",
                    "Read complete after",
                )
            )
        )

    if args.report or args.full_report:
        full_report = template.render(
            path=result.path,
            init_result=result.init_result(),
            check_result=result.check_result_msg(),
            fmt_result=result.fmt_result(),
            validate_result=result.validate_result(),
            plan_result=result.plan_result(),
            plan_output=result.plan_output,
            plan_msg=result.plan_msg(),
        )

        if args.full_report:
            args.full_report.write(full_report)

        report = full_report
        if len(full_report) > 65536:
            report = remove_plan(full_report)

        args.report.write(report)

    sys.exit(result.exitcode())
