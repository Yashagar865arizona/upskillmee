# Vercel Deployment Documentation for Ponder FastAPI Backend

This document details how to deploy the Ponder FastAPI backend on Vercel. Note that Vercel deploys backend code as serverless functions, so some restructuring of your FastAPI application may be required.

## 1. Overview

The Ponder FastAPI backend, which was previously deployed on AWS EC2 using a GitHub Actions workflow, will now be deployed as a serverless function on Vercel. This provides benefits such as automatic scaling, simplified deployment, and closer integration with GitHub.

## 2. Prerequisites

- Your FastAPI application should be structured to run as a serverless function. This typically means having an entry point file that Vercel can invoke (e.g., placing your code in an `api/` directory with a file such as `index.py`).
- Ensure you have a `requirements.txt` file listing all dependencies.

For example, your FastAPI application might look like:

```python
# File: api/index.py
from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def read_root():
    return {"message": "Hello from FastAPI on Vercel!"}
```

## 3. Setup Steps

### A. Reorganize Your Backend Code
- If your backend code currently resides in the `backend/` folder, create a new directory named `api` at the root of your repository (or inside `backend/` if preferred).
- Move (or symlink) your main FastAPI application file to `api/index.py` so that Vercel can automatically detect and deploy it as a serverless function.

### B. Add a Vercel Configuration File
- In the root of your backend project (or in your repository if you prefer a monorepo approach), create a file named `vercel.json` with the following content:

```json
{
  "functions": {
    "api/index.py": {
      "runtime": "python3.9"
    }
  },
  "rewrites": [
    { "source": "/(.*)", "destination": "/api/index.py" }
  ]
}
```

This `vercel.json` file does two things:
- It specifies that `api/index.py` should run with the Python 3.9 runtime.
- It rewrites all incoming requests to be handled by your FastAPI application, enabling a Single Page Application style of routing.

### C. Configure Environment Variables
- In the Vercel dashboard, add any environment variables your FastAPI app requires (e.g., database URLs, secret keys, etc.).

### D. Connect Your Repository to Vercel
- Create a new Vercel project for your backend.
- When prompted, set the project root to the directory containing your backend code (if using a monorepo, you might need to specify the build options accordingly).
- Vercel will detect your Python project based on the presence of a `requirements.txt` file and the runtime configuration in `vercel.json`.

## 4. Deployment Process

- On each push to the main branch, Vercel will automatically build and deploy your FastAPI backend as a serverless function.
- Use the Vercel dashboard to monitor deployment logs and verify that your API is functioning correctly.

## 5. Post-deployment Checks

- Access the Vercel-provided URL for your backend (e.g., `https://<your-vercel-backend>.vercel.app/`) to ensure the API is live.
- Use tools like `curl` or Postman to test the API endpoints.
- If you are using a custom domain for your backend, update the DNS settings accordingly.

## 6. Troubleshooting

- **Deployment Errors:** Check the deployment logs in the Vercel dashboard for any build errors or missing dependencies.
- **Routing Issues:** If the API endpoints are not working as expected, verify the rewrites configuration in `vercel.json`.
- **CORS and Environment Variables:** Ensure that environment variables and CORS settings (if needed) are correctly configured in your FastAPI app.

By following these steps, you can successfully migrate your FastAPI backend to a serverless deployment on Vercel, moving away from the previous AWS EC2 and GitHub Actions-based deployment process. 