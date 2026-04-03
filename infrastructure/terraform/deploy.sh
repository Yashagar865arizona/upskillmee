#!/bin/bash
set -e

# Check if AWS credentials are set
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "Error: AWS credentials not set"
    exit 1
fi

# Initialize Terraform
terraform init

# Create terraform.tfvars if it doesn't exist
if [ ! -f "terraform.tfvars" ]; then
    cat > terraform.tfvars << EOF
aws_region = "eu-north-1"
environment = "production"
app_name = "ponder"
domain_name = "ponder.school"
db_name = "ponder"
db_username = "ponder"
# Generate a random password for the database
db_password = "$(openssl rand -base64 32)"
EOF
fi

# Validate the configuration
terraform validate

# Create a plan
terraform plan -out=tfplan

# Ask for confirmation
read -p "Do you want to apply this plan? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Apply the configuration
    terraform apply tfplan
    
    # Output important information
    echo "Infrastructure deployment complete!"
    echo "Important outputs:"
    terraform output
fi
