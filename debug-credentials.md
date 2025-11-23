# AWS Credentials Troubleshooting

## Common Issues & Solutions

### 1. Invalid AWS Credentials
**Error:** "The request signature we calculated does not match the signature you provided"

**Solutions:**
- Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in GitHub secrets
- Ensure no extra spaces or characters in the secrets
- Check that the IAM user has necessary permissions

### 2. Required IAM Permissions
Your AWS user needs these permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:*",
                "ecs:*",
                "iam:*",
                "ec2:*",
                "logs:*",
                "sts:GetCallerIdentity"
            ],
            "Resource": "*"
        }
    ]
}
```

### 3. Test Credentials Locally
```bash
# Test your credentials
aws configure set aws_access_key_id YOUR_ACCESS_KEY
aws configure set aws_secret_access_key YOUR_SECRET_KEY
aws configure set region us-east-1

# Verify
aws sts get-caller-identity
```

### 4. GitHub Secrets Setup
1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Add these secrets:
   - `AWS_ACCESS_KEY_ID`: Your AWS access key
   - `AWS_SECRET_ACCESS_KEY`: Your AWS secret key

### 5. Create New IAM User (if needed)
```bash
# Create IAM user with required permissions
aws iam create-user --user-name github-actions-dynamodb-mcp

# Attach policy
aws iam attach-user-policy \
  --user-name github-actions-dynamodb-mcp \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Create access keys
aws iam create-access-key --user-name github-actions-dynamodb-mcp
```

### 6. Verify Repository Settings
- Ensure the repository is not a fork (GitHub Actions secrets don't work on forks)
- Check that Actions are enabled for the repository
- Verify the branch name matches the workflow trigger (main/master)