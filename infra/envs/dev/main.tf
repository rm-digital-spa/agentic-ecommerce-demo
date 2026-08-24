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

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

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

  statement {
    sid = "invokebedrock"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ]
    effect    = "Allow"
    resources = ["*"]
  }

  # AgentCore owns the log group itself (there is no logging argument on the
  # runtime resource); what gates it is whether this role may write there.
  # Like S3, CloudWatch Logs has two ARN shapes and the actions split across
  # them: CreateLogGroup acts on the group, the rest on the streams inside it.
  statement {
    sid = "createruntimeloggroup"
    actions = [
      "logs:CreateLogGroup",
      "logs:DescribeLogStreams"
    ]
    effect = "Allow"
    resources = [
      "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
    ]
  }

  statement {
    sid = "writeruntimelogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    effect = "Allow"
    resources = [
      "arn:aws:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
    ]
  }
}

resource "aws_iam_role" "agent_runtime_role" {
  name               = "ecommerce-agentcore-runtime-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy" "sii-mcp-role" {
  name   = "ecommerce-agentcore-runtime-policy"
  role   = aws_iam_role.agent_runtime_role.id
  policy = data.aws_iam_policy_document.ecr_permissions.json
}


locals {
  # api and sii-mcp image should not be use for agent core HTTP runtime
  agentcore_images = toset([for image_name in local.images : image_name if !strcontains(image_name, "api") && !strcontains(image_name, "sii-mcp")])
}

# must be declared outside each block as it will be referenced later
resource "aws_bedrockagentcore_agent_runtime" "sii_mcp" {

  agent_runtime_name = "ecommercesiimcp"

  role_arn = aws_iam_role.agent_runtime_role.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = data.aws_ecr_image.ecr_image["sii-mcp"].image_uri
    }
  }

  protocol_configuration {
    server_protocol ="MCP"
  }

  network_configuration {
    network_mode = "PUBLIC"
  }
}

resource "aws_bedrockagentcore_agent_runtime" "http_agent_runtime" {

  for_each = local.agentcore_images

  agent_runtime_name = replace("ecommerce${each.value}", "-", "")

  role_arn = aws_iam_role.agent_runtime_role.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = data.aws_ecr_image.ecr_image[each.value].image_uri
    }
  }

  environment_variables = {
    SII_AGENT_PORT : 8080
    ECOMMERCE_AGENT_PORT : 8080

    #  example url for agentcore mcp - https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    SII_MCP_URL = each.value == "sii-agent" ? "https://bedrock-agentcore.us-west-2.amazonaws.com/runtimes/${urlencode(aws_bedrockagentcore_agent_runtime.sii_mcp.agent_runtime_arn)}/invocations?qualifier=DEFAULT" : ""
  }

  protocol_configuration {
    // Only sii-mcp will use MCP protocol
    # server_protocol = each.value == "sii-mcp" ? "MCP" : "HTTP"
    server_protocol = "HTTP"
  }

  network_configuration {
    network_mode = "PUBLIC"
  }
}

resource "aws_s3_bucket" "kb_bucket" {
  bucket = "kb-bucket-${data.aws_caller_identity.current.account_id}"
}


data "aws_iam_policy_document" "ecommerceagent_user_memory_role_permissions" {
  statement {
    sid = "CloudWatchWritePermissionStatement"
    actions   = ["cloudwatch:PutMetricData"]
    effect    = "Allow"
    resources = ["*"]

    condition {
      test = "StringEquals"
      variable =  "cloudwatch:namespace"
      values = ["AWS/Bedrock/KnowledgeBases"]
    }
  }

  statement {
    sid = "S3ListBucketStatement"
    actions   = ["s3:ListBucket"]
    effect    = "Allow"
    resources = [
      #TODO: Need a bucket arn here
      # "*"
      aws_s3_bucket.kb_bucket.arn
    ]

    condition {
      test = "StringEquals"
      variable =  "cloudwatch:namespace"
      values = ["AWS/Bedrock/KnowledgeBases"]
    }
  }
}

resource "aws_iam_role" "ecommerceagent_user_memory_role" {
  name               = "ecommerceagent_user_memory_role"
  assume_role_policy = data.aws_iam_policy_document.ecommerceagent_user_memory_role_permissions.json
}

resource "aws_bedrockagent_knowledge_base" "ecommerceagent_user_memory" {
  name     = "ecommerceagent_user_memory"
  role_arn = aws_iam_role.ecommerceagent_user_memory_role.arn

  knowledge_base_configuration {
    type = "MANAGED"

    managed_knowledge_base_configuration {
      embedding_model_type = "MANAGED"
    }
  }
}

output "ecr_repository_uris" {
  value = { for k, v in aws_ecr_repository.repository : k => v.repository_url }
}


# moved {
#   from = aws_bedrockagentcore_agent_runtime.http_agent_runtime["sii-mcp"]
#   to = aws_bedrockagentcore_agent_runtime.sii_mcp
# }
