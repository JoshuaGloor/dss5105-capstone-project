# One-time setup, run from laptop with admin credentials.
# Creates what the main config and GitHub Actions need before they can run:
#   - S3 bucket for OpenTofu state
#   - GitHub OIDC provider + the deploy role

terraform {
  required_version = ">= 1.12"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

variable "project" {
  type    = string
  default = "dss5105"
}

variable "region" {
  type    = string
  default = "ap-southeast-1"
}

# Not plain "repo:owner/name". Repos created after 2026-07-15 get immutable
# subject claims, where owner and repo carry their numeric IDs, so a rename or
# transfer cannot hand this trust to a different repo. Read the live value with:
#   gh api /repos/<owner>/<repo>/actions/oidc/customization/sub
# Ref: https://github.blog/changelog/2026-04-23-immutable-subject-claims-for-github-actions-oidc-tokens/
variable "github_sub_prefix" {
  type        = string
  description = "Immutable OIDC subject prefix; the branch part is appended below."
  default     = "repo:JoshuaGloor@50296376/dss5105-capstone-project@1342683223"
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = var.project }
  }
}

data "aws_caller_identity" "me" {}

locals {
  account_id = data.aws_caller_identity.me.account_id
}

# ---------- OpenTofu state bucket ----------
# Remote backend for OpenTofu state, so there is one source of truth.

resource "aws_s3_bucket" "tfstate" {
  bucket        = "${var.project}-tfstate-${local.account_id}"
  force_destroy = true # Allow nuking once project is done.
  # Guard against accidental destroy during the project.
  # TODO(cleanup): remove before final `tofu destroy`.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "tfstate" {
  bucket = aws_s3_bucket.tfstate.id
  versioning_configuration {
    status = "Enabled"
  }
}

# New buckets block public access by default; declared explicitly so tofu detects and reverts drift.
resource "aws_s3_bucket_public_access_block" "tfstate" {
  bucket                  = aws_s3_bucket.tfstate.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------- GitHub OIDC ----------
# Trust policy: decides _who_ may put on the deploy role's "hat". See permissions policy below.
# Lets GitHub Actions deploy to AWS via OIDC, without long-lived access keys.
# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document#example-usage
#
# +-------------------+                       +--------------------+
# | GitHub Actions    | --  1. request   -->  | GitHub OIDC issuer |
# | job on main       | <-- 2. signed JWT --  | signs JWT          |
# +-------------------+                       +--------------------+
#           |
#           | 3. AssumeRoleWithWebIdentity(JWT)
#           v
# +--------------------------------------------+
# | AWS STS checks this trust policy:          |
# | - signature valid?  (via OIDC provider)    |
# | - aud == sts.amazonaws.com                 |
# | - sub == <sub prefix>:ref:refs/heads/main  |
# +--------------------------------------------+
#           |
#           | 4. temporary credentials (1h default)
#           v
#   deploy runs as the deploy role

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

# Only tokens from this repo, with a matching "sub" (subject) claim, can assume the role.
# Conditions use boolean "and".
data "aws_iam_policy_document" "deploy_trust" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }
    # Token must be issued for AWS Security Token Service (audience check).
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }
    # Which workflow runs may assume the role (subject check). Main only: both
    # jobs run from there, and a manual deploy dispatches main's copy anyway.
    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["${var.github_sub_prefix}:ref:refs/heads/main"]
    }
  }
}

# ---------- Deploy role: push images, run commands, start/stop ----------
# Permissions policy: decides _what_ the "hat" lets you do once worn. See trust policy above.

resource "aws_iam_role" "deploy" {
  name               = "${var.project}-github-deploy"
  assume_role_policy = data.aws_iam_policy_document.deploy_trust.json
}

# Each statement is one rule: "allow these actions on these resources (if these conditions hold)."
# Deliberately absent: any ssm:GetParameter permission. The deploy role must never
# be able to read the LLM API key. Only the instance reads it, at deploy time.
data "aws_iam_policy_document" "deploy" {
  # --- Image push iam ---
  # Ref: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-push-iam.html
  statement {
    sid       = "EcrLogin"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "EcrPush"
    actions = [
      "ecr:CompleteLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:InitiateLayerUpload",
      "ecr:BatchCheckLayerAvailability",
      "ecr:PutImage",
      "ecr:BatchGetImage",
    ]
    resources = ["arn:aws:ecr:${var.region}:${local.account_id}:repository/${var.project}-*"]
  }

  # --- EC2 start/stop ---
  # Ref: https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_examples_ec2_tag-owner.html
  statement {
    sid       = "FindInstance"
    actions   = ["ec2:DescribeInstances"]
    resources = ["*"]
  }

  statement {
    sid       = "StartStopOurInstanceOnly"
    actions   = ["ec2:StartInstances", "ec2:StopInstances"]
    resources = ["arn:aws:ec2:${var.region}:${local.account_id}:instance/*"]
    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/Project"
      values   = [var.project]
    }
  }

  # --- Run shell command (SSM Run Command) ---
  # Ref: https://docs.aws.amazon.com/systems-manager/latest/userguide/run-command-setting-up.html#tag-based-access
  statement {
    sid     = "RunShellScriptDocument"
    actions = ["ssm:SendCommand"]
    # AWS-RunShellScript: AWS-owned document that runs a list of shell commands as root.
    resources = ["arn:aws:ssm:${var.region}::document/AWS-RunShellScript"]
  }
  statement {
    sid       = "RunCommandOnOurInstanceOnly"
    actions   = ["ssm:SendCommand"]
    resources = ["arn:aws:ec2:${var.region}:${local.account_id}:instance/*"]
    condition {
      test     = "StringEquals"
      variable = "ssm:resourceTag/Project"
      values   = [var.project]
    }
  }

  # --- Poll status/output ---
  # SendCommand is async; this allows reading status and outputs.
  # Ref: https://docs.aws.amazon.com/systems-manager/latest/APIReference/API_GetCommandInvocation.html
  statement {
    sid       = "ReadCommandResults"
    actions   = ["ssm:GetCommandInvocation"]
    resources = ["*"]
  }
}

# Attach the permissions policy above to the deploy role (inline).
resource "aws_iam_role_policy" "deploy" {
  name   = "deploy"
  role   = aws_iam_role.deploy.id
  policy = data.aws_iam_policy_document.deploy.json
}

# ---------- Outputs: paste these into GitHub and tofu/main.tf ----------

output "state_bucket" {
  description = "Bucket name for the backend \"s3\" block in tofu/main.tf."
  value       = aws_s3_bucket.tfstate.bucket
}

output "deploy_role_arn" {
  description = "Set as GitHub repo variable AWS_DEPLOY_ROLE_ARN (used by role-to-assume)."
  value       = aws_iam_role.deploy.arn
}
