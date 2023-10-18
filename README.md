# terraform-check
`HENNGE/terraform-check` is a composite action (using Python in the back) to execute checks on Terraform configuration in your Github Actions workflow.

This action will execute the following Terraform commands:
1. `terraform init`
2. `terraform fmt`
3. `terraform validate`
4. `terraform plan`

The result and detailed report of the check will be returned as output of this action.
Optionally, the [detailed report](#detailed-report) can be automatically posted as PR comments.

## Usage
Make sure that your workflow already have the credentials needed by your Terraform configuration.
(e.g. authenticate to AWS with [aws-actions/configure-aws-credentials](https://github.com/aws-actions/configure-aws-credentials))
```yaml
steps:
- uses: HENNGE/terraform-check@v1
  with:
    directory: infra/tf
```

Specific Terraform version can be used:
```yaml
steps:
- uses: HENNGE/terraform-check@v1
  with:
    directory: infra/tf
    terraform_version: 1.1.7
```

If terraform is already installed, it can be used:
```yaml
steps:
- uses: HENNGE/terraform-check@v1
  with:
    directory: infra/tf
    terraform_version: system
```

Multiple directories can be set as input, separated by space:
```yaml
steps:
- uses: HENNGE/terraform-check@v1
  with:
    directory: infra/tf infra/tf2
```

If checking on multiple directories, you can set Terraform version for each directory:
```yaml
steps:
- uses: HENNGE/terraform-check@v1
  with:
    directory: infra/tf infra/tf2
    terraform_version: 1.1.7 1.3.4
```

If only one version is set, it will be used for all directories:
```yaml
steps:
- uses: HENNGE/terraform-check@v1
  with:
    directory: infra/tf infra/tf2
    terraform_version: 1.1.7
```

If checking directories, you can pass different plan arguments for each:
```yaml
steps:
- uses: HENNGE/terraform-check@v1
  with:
    directory: infra/tf infra/tf2
    plan_args: '["-var foo_version=${{ env.FOO_VERSION }}", ""]'
```

[Detailed report](#detailed-report) can be automatically posted as a pull request comment.
Make sure that Github token has permission to write into pull requests.
```yaml
permissions:
  contents: read
  pull-requests: write

# ... (omitted)

steps:
- uses: HENNGE/terraform-check@v1
  with:
    directory: infra/tf
    post_comment: true
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

If `post_comment` is set to `update`, the previous comment will be updated if the action runs again.
```yaml
steps:
- uses: HENNGE/terraform-check@v1
  with:
    directory: infra/tf
    post_comment: update
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

If `post_comment` is set to `nonzero`, comments will only be posted if return code is not zero (checks failed or there are changes).
```yaml
steps:
- uses: HENNGE/terraform-check@v1
  with:
    directory: infra/tf
    post_comment: nonzero
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Inputs

- `directory`: (required) One or more directories separated by space, containing the Terraform configuration.
- `terraform_version`: (optional) Terraform version to use. 
You can set version for each directory if checking on multiple directories. 
If set to `system`, the action will use the terraform version already installed.
Defaults to `latest`.
- `hide_refresh`: (optional) Hide state refresh output from report
- `post_comment`: (optional) Whether to post [detailed report](#detailed-report) as pull request comment. 
  - If set to `true`, will post a comment every time.
  - If set to `update`, will post a comment and then update the existing comment on any subsequent runs.
  - If set to `nonzero`, will post a comment only if any checks failed or there's changes to the Terraform plan ([returncode](#outputs) other than 0).
- `github_token`: (optional) Github access token, required to post PR comments.
- `issue_number`: (optional) If set, post comment to a specific issue or PR instead of the current one.
- `plan_args`: (optional) If set, additional arguments to pass to `terraform plan`.
Note that this is passed through as serialised json array, corresponding to the
array of directories passed. (This is so you can have different args per
terraform plan invocation). The strings will be passed directory into the shell,
so if you have spaces in variables you will need to quote them, but escape the
quotes (and then escape in json).

## Outputs

- `returncode` :
  - `0` if all checks passed.
  - `1` if any checks failed.
  - `2` if there's changes to the Terraform plan.
- `result`: Check result in the format of`Terraform check on <path> <result>`.
- `report`: [Detailed report](#detailed-report) in Github Markdown format of the check result including `terraform plan` output.

## Detailed report
The detailed report will look like this:

> ### Terraform check on infra/tf ✅Passed: there are no changes✅
>
> <details><summary>Show Details</summary>
>
> #### Terraform Init 🏗`success` 
> #### Terraform Format and Style 🖌`success`
> #### Terraform Validation 🤖`success`
> #### Terraform Plan 📖`success`✅Passed: there are no changes✅
> 
> <details><summary>Show Plan</summary>
> 
> ```terraform
> No changes. Your infrastructure matches the configuration.
> 
> Terraform has compared your real infrastructure against your configuration
> and found no differences, so no changes are needed.
> ```
> 
> </details>
> </details>

## Acknowledgment

- This action is inspired from [dflook/terraform-check](https://github.com/dflook/terraform-check)
- Detailed report format is adapted from [hashicorp/setup-terraform](https://github.com/hashicorp/setup-terraform)
