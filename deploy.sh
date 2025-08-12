#!/bin/bash
set -e

STACK_NAME="legalink-whatsapp-agent"
S3_BUCKET="legalink-deployment-artifacts" # Replace with your actual S3 bucket name
REGION="us-east-1" # Replace with your preferred AWS region

echo "Building and deploying Legalink WhatsApp Agent..."

# Create deployment package
echo "Creating deployment package..."
pip install -r requirements.txt --target ./package
cp -r app ./package/
cd package
zip -r ../deployment.zip .
cd ..

# Upload to S3
echo "Uploading deployment package to S3..."
aws s3 cp deployment.zip s3://$S3_BUCKET/legalink-whatsapp-agent/deployment.zip

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file infrastructure/template.yaml \
  --stack-name $STACK_NAME \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    S3Bucket=$S3_BUCKET \
    S3Key=legalink-whatsapp-agent/deployment.zip \
  --region $REGION

# Get the API Gateway URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query "Stacks[0].Outputs[?OutputKey=='ApiGatewayUrl'].OutputValue" \
  --output text \
  --region $REGION)

echo "Deployment completed successfully!"
echo "API Gateway URL: $API_URL"
