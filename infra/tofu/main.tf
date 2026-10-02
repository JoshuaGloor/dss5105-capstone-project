# The app infrastructure: one ECR repo, a security group, and one EC2 instance.
# Run bootstrap/ first: its state bucket is this config's backend, and its
# outputs supply the bucket name below.

terraform {
  required_version = ">= 1.12"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Backend blocks can't use variables, so we pasted the bootstrap "state_bucket"
  # output to "bucket" before the first `tofu init`.
  backend "s3" {
    bucket       = "dss5105-tfstate-472158500502"
    key          = "app/terraform.tfstate"
    region       = "ap-southeast-1"
    use_lockfile = true # S3-native locking.
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

variable "instance_type" {
  type    = string
  default = "t3.small" # 2 vCPU, 2 GB. Should be enough for Streamlit + Caddy.
}

variable "use_elastic_ip" {
  type        = bool
  default     = true
  description = "Keep one address across stop/start for simplicity."
}

variable "docker_compose_version" {
  type        = string
  default     = "v5.5.1"
  description = "Pinned so a rebuild later is reproducible and a bad upstream release cannot break a fresh instance."
}

provider "aws" {
  region = var.region
  default_tags {
    tags = { Project = var.project } # The deploy and power workflows find the instance by this tag.
  }
}

data "aws_caller_identity" "me" {}

locals {
  account_id = data.aws_caller_identity.me.account_id
}

# Use the account's default VPC; custom networking is out of scope.
data "aws_vpc" "default" {
  default = true
}

# al2027 in public preview, use al2023.
data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }
}

# ---------- Container registry ----------
# One repository: a single application image. Streamlit serves the UI and calls
# src/dss5105 in-process, so there is no second service to publish.

resource "aws_ecr_repository" "app" {
  name         = "${var.project}-app"
  force_delete = true # Allow nuking once project is done.

  # Basic scanning is free and reports CVEs per pushed image.
  # Ref: https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning-basic.html
  image_scanning_configuration {
    scan_on_push = true
  }
}

# Expire all but the 10 newest images; any deploy tag still here can be rolled back to instantly.
resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

# ---------- Network ----------
# Only 80/443 open. No SSH and no port 22: shell access is Session Manager.

resource "aws_security_group" "web" {
  name        = "${var.project}-web"
  description = "HTTP/HTTPS in, everything out. No SSH: use SSM Session Manager."
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound (ECR pulls, SSM, LLM provider APIs)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------- Instance trust ----------
# Trust policy: decides _who_ may put on the instance role's "hat". Here EC2 itself,
# unlike the deploy role in bootstrap/, which GitHub wears. See permissions below.

data "aws_iam_policy_document" "ec2_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# ---------- Instance policy ----------
# Permissions policy: decides _what_ the "hat" lets you do once worn. See trust policy above.

resource "aws_iam_role" "instance" {
  name               = "${var.project}-instance"
  assume_role_policy = data.aws_iam_policy_document.ec2_trust.json
}

# SSM agent registration (Session Manager, Run Command) and pulling from ECR.
resource "aws_iam_role_policy_attachment" "instance" {
  # These policies are AWS-managed.
  for_each = toset([
    "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore",
    "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
  ])
  role       = aws_iam_role.instance.name
  policy_arn = each.value
}

# The LLM API key reaches the server here and nowhere else: never through GitHub
# Actions, so no log can leak it, and not in OpenTofu state.
data "aws_iam_policy_document" "instance_secrets" {
  # Read this project's own config.
  statement {
    sid       = "ReadOwnConfig"
    actions   = ["ssm:GetParameter", "ssm:GetParameters"]
    resources = ["arn:aws:ssm:${var.region}:${local.account_id}:parameter/${var.project}/prod/*"]
  }

  # Decrypt it, but only when SSM is the caller.
  # Ref: https://docs.aws.amazon.com/kms/latest/developerguide/conditions-kms.html#conditions-kms-via-service
  statement {
    sid       = "DecryptViaSsmOnly"
    actions   = ["kms:Decrypt"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ssm.${var.region}.amazonaws.com"]
    }
  }
}

# Attach the permissions policy above to the instance role (inline).
resource "aws_iam_role_policy" "instance_secrets" {
  name   = "read-app-config"
  role   = aws_iam_role.instance.id
  policy = data.aws_iam_policy_document.instance_secrets.json
}

# An instance profile is the wrapper that lets EC2 wear the role above.
resource "aws_iam_instance_profile" "instance" {
  name = "${var.project}-instance"
  role = aws_iam_role.instance.name
}

# ---------- The server ----------

resource "aws_instance" "app" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  iam_instance_profile   = aws_iam_instance_profile.instance.name
  vpc_security_group_ids = [aws_security_group.web.id]

  # user_data is the init script.
  # Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/user-data.html
  user_data = templatefile("${path.module}/user_data.sh", {
    docker_compose_version = var.docker_compose_version
    # compose_arch follows the AMI that was actually selected, so the plugin binary
    # cannot disagree with the machine. Compose says aarch64 where AWS says arm64.
    compose_arch = data.aws_ami.al2023.architecture == "arm64" ? "aarch64" : "x86_64"
  })

  # user_data only runs on first boot, so editing user_data.sh or bumping
  # docker_compose_version has no effect unless the instance is replaced.
  # Replacement wipes /opt/app AND the docker volume holding confirmed
  # allocations and live queue state, so it is data loss and downtime.
  # Export the records from the app first. Stop/start is safe; only replacement is not.
  # The Elastic IP re-associates, so the URL itself survives.
  # On update of user_data, this causes downtime, which is ok for this school project.
  user_data_replace_on_change = true

  # IMDSv2 only: metadata requires a session token, which mitigates SSRF-based credential theft.
  # Ref: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html
  metadata_options {
    http_tokens = "required"
  }

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = { Name = "${var.project}-app" }

  lifecycle {
    # A newer AMI appears every few weeks; don't rebuild the server just for that.
    ignore_changes = [ami]
  }
}

resource "aws_eip" "app" {
  count    = var.use_elastic_ip ? 1 : 0
  instance = aws_instance.app.id
  domain   = "vpc"
}

# ---------- Outputs ----------

locals {
  public_ip = var.use_elastic_ip ? aws_eip.app[0].public_ip : aws_instance.app.public_ip
}

output "instance_id" {
  description = "The instance ID. Start/stop finds it using the project tag."
  value       = aws_instance.app.id
}

output "public_ip" {
  description = "Stable across stop/start while use_elastic_ip is true. Point a domain here."
  value       = local.public_ip
}

output "app_url" {
  description = "Address while there is no domain. Set SITE_ADDRESS and Caddy serves https://<domain> instead."
  value       = "http://${local.public_ip}"
}

output "ecr_repository" {
  description = "Repository the deploy workflow pushes images to."
  value       = aws_ecr_repository.app.repository_url
}
