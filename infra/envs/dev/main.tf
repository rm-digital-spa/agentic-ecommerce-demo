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
    # awscc = {
    #      source  = "hashicorp/awscc"
    #      version = "~> 1.0"
    # }
  }
}

provider "aws" {
  # region = "us-east-1"
}

# provider "awscc" {

# }

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
      type = "Service"
      identifiers = [
        "bedrock-agentcore.amazonaws.com"
      ]
    }
  }
}

# "Unable to assume the given role" is a trust-policy error, not a permissions
# one. Knowledge bases are assumed by bedrock.amazonaws.com; the agent runtimes
# above are assumed by bedrock-agentcore.amazonaws.com. Different service
# principals, so they cannot share one trust document.
#
# The two conditions are the standard confused-deputy guard: without them, any
# account that can name this role's ARN could induce Bedrock to assume it on
# their behalf. SourceAccount pins the caller; SourceArn pins it to knowledge
# bases in this account rather than any Bedrock resource.
data "aws_iam_policy_document" "bedrock_kb_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["bedrock.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:bedrock:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:knowledge-base/*"]
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

  vector_dimension = 256
  vector_data_type = "float32"

  # Single-sourced because two resources must agree on it: the knowledge base
  # embeds with this model, and the role policy below grants InvokeModel on it.
  embedding_model_arn = "arn:aws:bedrock:${data.aws_region.current.region}::foundation-model/amazon.titan-embed-text-v2:0"
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
    server_protocol = "MCP"
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

resource "aws_s3_bucket" "kb_ds_bucket" {
  bucket = "kbds-bucket-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3vectors_vector_bucket" "kb_bucket" {
  vector_bucket_name = "kb-bucket-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3vectors_index" "kb_bucket_index" {
  index_name         = "${aws_s3vectors_vector_bucket.kb_bucket.vector_bucket_name}-index"
  vector_bucket_name = aws_s3vectors_vector_bucket.kb_bucket.vector_bucket_name

  data_type       = local.vector_data_type
  dimension       = local.vector_dimension
  distance_metric = "euclidean"
}


# The knowledge base's own service role. Bedrock assumes this to embed chunks
# and to read/write the vector index. It is NOT the role the agent container
# runs as when it calls Retrieve — that one is agent_runtime_role above.
data "aws_iam_policy_document" "ecommerceagent_user_memory_role_permissions" {
  statement {
    sid       = "CloudWatchWritePermissionStatement"
    actions   = ["cloudwatch:PutMetricData"]
    effect    = "Allow"
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["AWS/Bedrock/KnowledgeBases"]
    }
  }

  # Bedrock embeds on both paths — every chunk it ingests and every query it
  # retrieves for — so the knowledge base role needs the model in its own right,
  # independently of the agent runtime's InvokeModel grant.
  statement {
    sid       = "InvokeEmbeddingModel"
    actions   = ["bedrock:InvokeModel"]
    effect    = "Allow"
    resources = [local.embedding_model_arn]
  }

  # S3 Vectors is its own service with its own action namespace: none of the
  # s3:* actions apply to a vector bucket, which is why the previous
  # s3:ListBucket grant here was a no-op.
  #
  # Writes happen at ingestion, reads at retrieval, and deletes when a document
  # is removed from the data source — so the index needs all three.
  statement {
    sid    = "VectorIndexReadWrite"
    effect = "Allow"
    actions = [
      "s3vectors:GetIndex",
      "s3vectors:QueryVectors",
      "s3vectors:PutVectors",
      "s3vectors:GetVectors",
      "s3vectors:ListVectors",
      "s3vectors:DeleteVectors",
    ]
    resources = [aws_s3vectors_index.kb_bucket_index.index_arn]
  }

  # S3 Bucket data source permissions
  statement {
    sid = "S3BucketOps"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = [
      aws_s3_bucket.kb_ds_bucket.arn,
      "${aws_s3_bucket.kb_ds_bucket.arn}/*"
    ]
  }

  # Bucket-level actions take the bucket ARN, not the index ARN — the same
  # two-ARN-shapes split as CloudWatch Logs above.
  statement {
    sid       = "VectorBucketRead"
    effect    = "Allow"
    actions   = ["s3vectors:GetVectorBucket"]
    resources = [aws_s3vectors_vector_bucket.kb_bucket.vector_bucket_arn]
  }
}

resource "aws_iam_role" "ecommerceagent_user_memory_role" {
  name               = "ecommerceagent_user_memory_role"
  assume_role_policy = data.aws_iam_policy_document.bedrock_kb_assume_role.json
}

resource "aws_iam_role_policy" "ecommerceagent_user_memory_role_policy" {
  name   = "ecommerceagent-user-memory-role-policy"
  role   = aws_iam_role.ecommerceagent_user_memory_role.id
  policy = data.aws_iam_policy_document.ecommerceagent_user_memory_role_permissions.json
}

data "aws_bedrock_foundation_models" "models" {
  by_output_modality = "EMBEDDING"
}

resource "aws_bedrockagent_knowledge_base" "ecommerceagent_user_memory_kb" {
  name     = "ecommerceagent-user-memory-kb"
  role_arn = aws_iam_role.ecommerceagent_user_memory_role.arn

  knowledge_base_configuration {
    vector_knowledge_base_configuration {
      # Not sure if this filter is the safest way to get the embedding model arn, but it works for now. We can also hardcode the arn if needed.
      # embedding_model_arn = [for model_summary in data.aws_bedrock_foundation_models.models.model_summaries : model_summary.model_arn if strcontains(model_summary.model_id , "amazon.titan-embed-text-v2:0")][0]
      # embedding_model_arn = "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v2:0"
      embedding_model_arn = local.embedding_model_arn
      embedding_model_configuration {
        bedrock_embedding_model_configuration {
          dimensions          = local.vector_dimension
          embedding_data_type = upper(local.vector_data_type)
        }
      }
    }
    type = "VECTOR"
  }

  storage_configuration {
    type = "S3_VECTORS"
    s3_vectors_configuration {
      index_arn = aws_s3vectors_index.kb_bucket_index.index_arn
    }
  }
}

resource "aws_bedrockagent_data_source" "ecommerceagent_user_memory_kb_ds" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.ecommerceagent_user_memory_kb.id
  name              = "ecommerceagent-user-memory-kb-ds"
  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn = aws_s3_bucket.kb_ds_bucket.arn
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
