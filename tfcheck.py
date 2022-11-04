import argparse
import os
import subprocess
import sys
from dataclasses import dataclass

from jinja2 import Environment, FileSystemLoader

FMT_CMD = "terraform fmt -check=true -write=false -recursive -diff"
INIT_CMD = "terraform init -no-color"
VALIDATE_CMD = "terraform validate -no-color"
PLAN_CMD = "terraform plan -detailed-exitcode -no-color"

parser = argparse.ArgumentParser()
parser.add_argument("path", help="path to run terraform checks", nargs="+", type=str)
parser.add_argument(
    "-report",
    help="print detailed report to a file",
    type=argparse.FileType("w", encoding="UTF-8"),
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
            return "⚠️There are changes: see details⚠"


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


def check(path: str) -> CheckResult:
    # Terraform init
    init = run(INIT_CMD, path)

    # Terraform fmt
    fmt = run(FMT_CMD, path)

    # Terraform validate
    validate = run(VALIDATE_CMD, path)

    # Terraform plan
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


def render(results: list[CheckResult]) -> str:
    outputs = []
    for result in results:
        outputs.append(
            template.render(
                path=result.path,
                init_result=result.init_result(),
                check_result=result.check_result_msg(),
                fmt_result=result.fmt_result(),
                validate_result=result.validate_result(),
                plan_result=result.plan_result(),
                plan_output=result.plan_output,
                plan_msg=result.plan_msg(),
            )
        )

    return "\n\n---\n\n".join(outputs)


if __name__ == "__main__":
    args = parser.parse_args()

    results = []
    exitcode = 0
    for path in args.path:
        result = check(path)
        results.append(result)
        # Set exitcode to 1 if any check is failed
        # Set exitcode to 2 if any check contains plan change
        if exitcode == 0:
            exitcode = result.exitcode()
        elif exitcode == 2:
            exitcode = 1 if result.exitcode() == 1 else 2
        print(f"Terraform check on {path} {result.check_result_msg()}")

    rendered = render(results)
    if args.report:
        args.report.write(rendered)

    sys.exit(exitcode)
