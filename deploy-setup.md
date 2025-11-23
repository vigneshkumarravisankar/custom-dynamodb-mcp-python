# Deployment Setup Guide

## Prerequisites

1. **GitHub Repository** - Push your code to GitHub
2. **AWS Account** with appropriate permissions
3. **GitHub Secrets** configured

## Required GitHub Secrets

Add only these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

```
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

All other infrastructure (VPC, subnets, security groups, IAM roles) is created automatically by Terraform.

## Setup Steps

### 1. Push to GitHub (Infrastructure is created automatically)

```bash
git add .
git commit -m "Add DynamoDB MCP Server"
git push origin main
```

## Deployment Flow

1. **Push to GitHub** → Triggers GitHub Actions
2. **Build Docker Image** → Push to ECR
3. **Deploy to ECS** → Run container on Fargate
4. **Bedrock Agent** → Connect to MCP server

## Access Points

- **ECS Service**: `http://TASK_PUBLIC_IP:8000`
- **Health Check**: `http://TASK_PUBLIC_IP:8000/health`
- **MCP Endpoint**: `http://TASK_PUBLIC_IP:8000/mcp`

## Bedrock Agent Integration

1. Create Bedrock Agent using `bedrock-agent.json`
2. Configure action group to call your ECS service
3. Test with natural language queries

## Monitoring

- **CloudWatch Logs**: `/ecs/dynamodb-mcp-server`
- **ECS Console**: Monitor service health
- **ECR Console**: View Docker images

## Troubleshooting

- Check GitHub Actions logs for deployment issues
- Verify ECS task is running and healthy
- Ensure security groups allow port 8000
- Check CloudWatch logs for application errors