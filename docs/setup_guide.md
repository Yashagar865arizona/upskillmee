# Ponder Setup Guide

This guide will walk you through setting up and running Ponder on your computer, even if you're not familiar with programming. Follow each step carefully.

## Prerequisites

### 1. Install Python
1. Visit [Python's official website](https://www.python.org/downloads/)
2. Download Python 3.11 or later for your operating system
3. Run the installer
   - On Windows: Make sure to check "Add Python to PATH" during installation
   - On Mac: Double-click the downloaded package and follow the installation wizard

### 2. Install Node.js
1. Visit [Node.js website](https://nodejs.org/)
2. Download the LTS (Long Term Support) version
3. Run the installer and follow the prompts

### 3. Install PostgreSQL
1. Visit [PostgreSQL Downloads](https://www.postgresql.org/download/)
2. Download the installer for your operating system
3. Run the installer
   - Remember the password you set during installation
   - Default port (5432) is fine
   - When asked, select your country/locale

### 4. Install Git
1. Visit [Git Downloads](https://git-scm.com/downloads)
2. Download and run the installer for your system
3. Use default settings during installation

## Setting Up the Project

### 1. Get the Code
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

### 2. Set Up the Backend

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
   - Create `backend/.env.production` (similar to development)

4. Set up the database:
   ```bash
   # Create database
   createdb ponder_dev

   # Run migrations
   alembic upgrade head
   ```

### 3. Set Up the Frontend

1. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Create environment files:
   - Create `frontend/.env.local`:
   ```
   REACT_APP_API_URL=http://localhost:8000
   ```

## Running the Application

### 1. Start the Backend
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

### 2. Start the Frontend
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

## Common Issues and Solutions

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
