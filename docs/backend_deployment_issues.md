# Backend Deployment Issues on Vercel

## Overview
This document provides an overview of the issues encountered during the deployment of our FastAPI backend on Vercel. Despite multiple configuration attempts, we are still facing a persistent "404: NOT_FOUND" error.

## Error Encountered
- **Error Message Example:**
  ```
  404: NOT_FOUND
  Code: NOT_FOUND
  ID: dev1::5g6kg-1739281711984-b3771a2e9277
  ```

## Symptoms
- Local deployment using `vercel dev` returns a 404 error.
- Requests to the expected endpoint do not reach the FastAPI application.

## Timeline & Attempts to Resolve
1. **Initial Configuration (Rust Deployment Attempt):**
   - The initial `vercel.json` was configured to use a Rust builder (`now-rust`) with a reference to `Cargo.toml`.
   - **Issue:** Vercel warned that the build did not match any source files, as no Rust files were present.

2. **Reconfiguration for Python FastAPI Deployment:**
   - Updated `vercel.json` to use the `@vercel/python` builder, targeting the FastAPI entry point in `api/index.py`.
   - Created an `index.py` file in the project root (`ponder/backend/index.py`) that imports the FastAPI app from `api/index.py` and exposes it as `handler`.
   - Added `handler = app` in `api/index.py` to ensure the function is correctly exported.
   - **Result:** Despite these changes, the deployment still returns a 404 error.

3. **Additional Adjustments:**
   - Multiple attempts were made to adjust rewrite rules in `vercel.json` (with and without file extensions).
   - The routing error persisted regardless of these changes.

## Current Configuration
- **Function Entrypoint:**
  - **File:** `ponder/backend/index.py`
  - **Content:**
    ```python
    from api.index import app as handler
    ```

- **API Handler:**
  - **File:** `ponder/backend/api/index.py`
  - **Content:** Ends with `handler = app`

- **Vercel Configuration:**
  - **File:** `ponder/backend/vercel.json`
  - **Content:**
    ```json
    {
      "version": 2,
      "builds": [
        { "src": "index.py", "use": "@vercel/python" }
      ]
    }
    ```

- **Deployment Error Message:**
  - 404: NOT_FOUND (e.g., Code: NOT_FOUND, ID: dev1::5g6kg-1739281711984-b3771a2e9277)

## Potential Causes & Considerations
- There may be a mismatch in the routing configuration between Vercel and our FastAPI application.
- Vercel's Python builder might expect a different structure or function export method.
- The `.vercelignore` file seems correctly configured, but it is always worth verifying that essential files are not being excluded.

## Conclusion & Next Steps
- Despite several configuration changes (e.g., switching from now-rust to @vercel/python, modifying rewrites, and creating a separate entrypoint), the backend continues to return a 404 error.
- A thorough review of Vercel's latest documentation on deploying Python serverless functions is recommended.
- This document should help a new developer quickly understand the problem context, the steps already taken, and where further investigation is needed. 