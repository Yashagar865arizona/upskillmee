# Ponder

A modern career mentorship and psychometric testing platform.

## Project Structure

```
ponder/
├── backend/                 # Backend services
│   ├── tests/              # Backend test files
│   ├── scripts/            # Backend utility scripts
│   └── docs/               # Backend documentation
├── frontend/               # Frontend application
│   ├── tests/             # Frontend test files
│   ├── scripts/           # Frontend utility scripts
│   └── docs/              # Frontend documentation
├── infrastructure/         # Infrastructure and deployment
│   ├── k8s/               # Kubernetes configurations
│   ├── terraform/         # Terraform configurations
│   ├── docker-compose.yml # Docker compose configuration
│   └── ponder.service     # Systemd service file
├── docs/                  # Project documentation
│   ├── Ponder_Career_Mentor_Product_Plan.md
│   ├── Psychometric_Test_Product_Plan.md
│   └── module_plan.md
└── scripts/               # Project-wide utility scripts
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ponder.git
cd ponder
```

2. Set up the backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Start the development servers:
```bash
# Backend
cd backend
uvicorn main:app --reload

# Frontend
cd frontend
npm run dev
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## Deployment

See `infrastructure/` directory for deployment configurations:
- Kubernetes manifests in `infrastructure/k8s/`
- Terraform configurations in `infrastructure/terraform/`
- Docker Compose setup in `infrastructure/docker-compose.yml`

## Documentation

- Product plans and module documentation are in the `docs/` directory
- API documentation is available at `/api/docs` when running the backend server
- Frontend documentation is in `frontend/docs/`

## Contributing

1. Create a new branch for your feature
2. Make your changes
3. Write tests for your changes
4. Submit a pull request

## License

[Your License Here] 