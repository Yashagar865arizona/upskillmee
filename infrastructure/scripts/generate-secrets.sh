#!/bin/bash
# Script to generate secure secrets for production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔐 Generating secure secrets for Ponder production deployment${NC}"

# Function to generate random string
generate_secret() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Function to generate JWT secret
generate_jwt_secret() {
    openssl rand -base64 64 | tr -d "=+/" | cut -c1-64
}

# Create secrets directory if it doesn't exist
mkdir -p ../secrets

# Generate secrets
JWT_SECRET=$(generate_jwt_secret)
ADMIN_API_KEY=$(generate_secret)
POSTGRES_PASSWORD=$(generate_secret)
REDIS_PASSWORD=$(generate_secret)
GRAFANA_ADMIN_PASSWORD=$(generate_secret)

# Create secrets file
cat > ../secrets/production.env << EOF
# Generated secrets for production deployment
# Generated on: $(date)
# 
# IMPORTANT: 
# - Keep this file secure and never commit it to version control
# - Use a proper secrets management system in production (e.g., HashiCorp Vault, AWS Secrets Manager)
# - Rotate these secrets regularly

# Security Secrets
JWT_SECRET=${JWT_SECRET}
ADMIN_API_KEY=${ADMIN_API_KEY}

# Database Secrets
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

# Cache Secrets
REDIS_PASSWORD=${REDIS_PASSWORD}

# Monitoring Secrets
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}

# AI Service Keys (REPLACE WITH YOUR ACTUAL KEYS)
OPENAI_API_KEY=your-production-openai-key-here
DEEPSEEK_API_KEY=your-production-deepseek-key-here
ANTHROPIC_API_KEY=your-production-anthropic-key-here
XAI_API_KEY=your-production-xai-key-here
TOGETHER_API_KEY=your-production-together-key-here
MISTRAL_API_KEY=your-production-mistral-key-here
GEMINI_API_KEY=your-production-gemini-key-here

# Vector Database Keys
PINECONE_API_KEY=your-production-pinecone-key-here
EOF

# Set proper permissions
chmod 600 ../secrets/production.env

echo -e "${GREEN}✅ Secrets generated successfully!${NC}"
echo -e "${YELLOW}📁 Secrets saved to: infrastructure/secrets/production.env${NC}"
echo -e "${RED}⚠️  IMPORTANT SECURITY NOTES:${NC}"
echo -e "${RED}   - Never commit the secrets file to version control${NC}"
echo -e "${RED}   - Replace AI service keys with your actual production keys${NC}"
echo -e "${RED}   - Use a proper secrets management system in production${NC}"
echo -e "${RED}   - Rotate secrets regularly${NC}"

# Create .gitignore for secrets directory
cat > ../secrets/.gitignore << EOF
# Ignore all secrets files
*.env
*.key
*.pem
*.crt
*secret*
*password*
EOF

echo -e "${GREEN}🔒 Created .gitignore for secrets directory${NC}"

# Display next steps
echo -e "${YELLOW}"
echo "📋 Next steps:"
echo "1. Review and update the generated secrets file"
echo "2. Replace placeholder AI service keys with your actual keys"
echo "3. Copy the secrets to your production environment"
echo "4. Set up proper secrets management for production"
echo "5. Configure SSL certificates for HTTPS"
echo -e "${NC}"