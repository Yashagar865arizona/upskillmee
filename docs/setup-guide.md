# Ponder Setup Guide

This comprehensive guide will help you set up and run the Ponder AI mentorship platform locally. Choose the setup method that best fits your experience level.

## Quick Start (Experienced Developers)

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Git

### Backend Setup
```bash
# Clone and setup virtual environment
git clone https://github.com/yourusername/ponder.git
cd ponder/backend
python -m venv .venv
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env.development
# Edit .env.development with your database and OpenAI API credentials

# Setup database
createdb ponder_dev
alembic upgrade head

# Run server
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd ../frontend

# Install dependencies
npm install

# Setup environment
cp .env.example .env.local
# Edit .env.local if needed

# Run development server
npm start
```

Visit http://localhost:3000 to use the application.

## Detailed Setup (Step-by-Step)

### 1. Install Prerequisites

#### Python
1. Visit [Python's official website](https://www.python.org/downloads/)
2. Download Python 3.11 or later for your operating system
3. Run the installer
   - On Windows: Make sure to check "Add Python to PATH" during installation
   - On Mac: Double-click the downloaded package and follow the installation wizard

#### Node.js
1. Visit [Node.js website](https://nodejs.org/)
2. Download the LTS (Long Term Support) version
3. Run the installer and follow the prompts

#### PostgreSQL
1. Visit [PostgreSQL Downloads](https://www.postgresql.org/download/)
2. Download the installer for your operating system
3. Run the installer
   - Remember the password you set during installation
   - Default port (5432) is fine
   - When asked, select your country/locale

#### Git
1. Visit [Git Downloads](https://git-scm.com/downloads)
2. Download and run the installer for your system
3. Use default settings during installation

### 2. Get the Project Code

1. Open Terminal (Mac) or Command Prompt (Windows)
2. Navigate to where you want to store the project:
   ```bash
   cd Documents
   ```
3. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ponder.git
   cd ponder
   ```

### 3. Set Up the Backend

1. Create a virtual environment:
   ```bash
   # On Mac/Linux:
   python3 -m venv backend/.venv
   source backend/.venv/bin/activate

   # On Windows:
   python -m venv backend\.venv
   backend\.venv\Scripts\activate
   ```

2. Install backend dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Create environment files:
   - Create `backend/.env.development` with:
   ```
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/ponder_dev
   OPENAI_API_KEY=your_openai_api_key
   ```

4. Set up the database:
   ```bash
   # Create database
   createdb ponder_dev

   # Run migrations
   alembic upgrade head
   ```

### 4. Set Up the Frontend

1. Install frontend dependencies:
   ```bash
   cd ../frontend
   npm install
   ```

2. Create environment files:
   - Create `frontend/.env.local`:
   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

## Running the Application

### Start the Backend
1. Open a new terminal window
2. Navigate to the project:
   ```bash
   cd ponder/backend
   ```
3. Activate the virtual environment:
   ```bash
   # On Mac/Linux:
   source .venv/bin/activate
   # On Windows:
   .venv\Scripts\activate
   ```
4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```
   The backend will run on http://localhost:8000

### Start the Frontend
1. Open another terminal window
2. Navigate to the frontend directory:
   ```bash
   cd ponder/frontend
   ```
3. Start the development server:
   ```bash
   npm start
   ```
   The frontend will open automatically in your browser at http://localhost:3000

## Environment Variables

### Backend (.env.development)
```
# Database
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/ponder_dev

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Application
APP_ENV=development
DEBUG=true
SECRET_KEY=your_secret_key

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env.local)
```
REACT_APP_API_URL=http://localhost:8000
```

## Development Commands

### Backend
```bash
# Create new migration
alembic revision -m "description"

# Run migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Run tests
pytest

# Run with specific environment
ENVIRONMENT=development uvicorn app.main:app --reload
```

### Frontend
```bash
# Run tests
npm test

# Build for production
npm run build

# Run linting
npm run lint
```

## Project Structure

```
ponder/
├── backend/
│   ├── alembic/          # Database migrations
│   ├── app/
│   │   ├── agents/       # AI agent system
│   │   ├── api/          # API endpoints
│   │   ├── config/       # Configuration settings
│   │   ├── database/     # Database setup
│   │   ├── models/       # Database models
│   │   ├── services/     # Business logic
│   │   └── main.py       # FastAPI application
│   └── tests/            # Backend tests
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── api/          # API services
│   │   └── App.js        # Main React app
│   └── public/           # Static assets
├── infrastructure/       # Docker and deployment configs
└── docs/                 # Documentation
```

## Troubleshooting

### Database Connection Issues
- Make sure PostgreSQL is running
- Check if the database exists: `psql -l`
- Verify your database password in `.env.development`

### Node.js Errors
- Try deleting `node_modules` folder and `package-lock.json`
- Run `npm install` again

### Python/Backend Errors
- Make sure virtual environment is activated (you should see (.venv) in terminal)
- Try `pip install -r requirements.txt` again
- Check if all environment variables are set correctly

### OpenAI API Issues
- Verify your API key is correct
- Check if you have billing set up on OpenAI

## Getting Help

If you encounter any issues:
1. Check the error message in the terminal
2. Look for error logs in `backend/logs` directory
3. Make sure all services (PostgreSQL, backend, frontend) are running
4. Try stopping and restarting the servers

## Updating the Application

To get the latest updates:
1. Save any changes you've made
2. Pull the latest code:
   ```bash
   git pull origin main
   ```
3. Update dependencies:
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   alembic upgrade head

   # Frontend
   cd ../frontend
   npm install
   ```

## Security Notes

1. Never share your `.env` files or API keys
2. Keep your PostgreSQL password secure
3. Don't expose the backend port (8000) to the internet
4. Regularly update dependencies for security fixes

## Key Features

1. **AI Mentorship**
   - Personalized learning paths
   - Project-based learning
   - Real-time chat with AI mentor

2. **Progress Tracking**
   - Skill development monitoring
   - Project completion tracking
   - Learning pace analysis

3. **Metrics and Analytics**
   - Engagement metrics
   - Learning effectiveness
   - Mentor performance tracking

## Development Guidelines

1. **Code Style**
   - Backend: Follow PEP 8 guidelines
   - Frontend: Follow ESLint configuration
   - Use meaningful variable names and add comments for complex logic

2. **Testing**
   ```bash
   # Run backend tests
   cd backend
   pytest

   # Run frontend tests
   cd frontend
   npm test
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.