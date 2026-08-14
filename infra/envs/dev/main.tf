terraform {
  backend "s3" {
    bucket       = "agentic-ecommerce-demo-infra-state"
    region       = "us-east-1"
    key          = "dev/terraform.tfstate"
    use_lockfile = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  # region = "us-east-1"
}

locals {
  images = toset(["api", "ecommerce-agent", "sii-agent", "sii-mcp"])
}

resource "aws_ecr_repository" "repository" {
  name                 = "agentic-ecommerce-demo/${each.key}"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  for_each = local.images
}

# only keep the latest 5 images in the repository
resource "aws_ecr_lifecycle_policy" "lifecycle_policy" {
  for_each   = aws_ecr_repository.repository
  repository = aws_ecr_repository.repository[each.key].name
  policy     = <<EOF
{
  "rules": [
    {
      "rulePriority": 1,
      "description": "Keep only the latest 5 images",
      "selection": {
        "tagStatus": "any",
        "countType": "imageCountMoreThan",
        "countNumber": 5
      },
      "action": {
        "type": "expire"
      }
    }
  ]
}
EOF
}

# Iterating over the repository resource (rather than over local.images with a
# literal name) does two things: it single-sources the naming convention, and
# it creates the dependency edge so Terraform never tries to read an image
# before its repository exists.
#
# The `latest` tag is the promotion pointer; what we consume is its immutable
# digest, so a new push produces a real diff and deployments stay pinned.
data "aws_ecr_image" "ecr_image" {
  for_each = aws_ecr_repository.repository

  repository_name = each.value.name
  image_tag       = "latest"
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }
  }
}

// allow the role to pull images from ECR
data "aws_iam_policy_document" "ecr_permissions" {
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    effect    = "Allow"
    resources = ["*"]
  }

  statement {
    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer"
    ]
    effect    = "Allow"
    resources = [for r in aws_ecr_repository.repository : r.arn]
  }
}

resource "aws_iam_role" "sii-mcp-role" {
  name               = "ecommerce-agentcore-runtime-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy" "sii-mcp-role" {
  name   = "ecommerce-agentcore-runtime-policy"
  role   = aws_iam_role.sii-mcp-role.id
  policy = data.aws_iam_policy_document.ecr_permissions.json
}

resource "aws_bedrockagentcore_agent_runtime" "sii-mcp" {
  agent_runtime_name = "ecommercesiimcp"

  role_arn = aws_iam_role.sii-mcp-role.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = data.aws_ecr_image.ecr_image["sii-mcp"].image_uri
    }
  }

  protocol_configuration {
    server_protocol = "MCP"
  }

  network_configuration {
    network_mode = "PUBLIC"
  }
}

output "ecr_repository_uris" {
  value = { for k, v in aws_ecr_repository.repository : k => v.repository_url }
}
