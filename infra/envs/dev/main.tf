terraform {
  backend "s3" {
    bucket = "agentic-ecommerce-demo-infra-state"
    region = "us-east-1"
    key = "dev/terraform.tfstate"
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
  name = each.key
  image_tag_mutability = "MUTABLE"
  force_delete = true

  for_each = local.images
}

# only keep the latest 5 images in the repository
resource "aws_ecr_lifecycle_policy" "lifecycle_policy" {
  for_each = aws_ecr_repository.repository
  repository = aws_ecr_repository.repository[each.key].name
  policy = <<EOF
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


output "ecr_repository_uris" {
  value = { for k, v in aws_ecr_repository.repository : k => v.repository_url }
}
