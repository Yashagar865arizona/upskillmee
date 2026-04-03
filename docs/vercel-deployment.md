# Vercel Deployment Documentation for Ponder React Frontend

This document details how to deploy the Ponder React frontend on Vercel while keeping the WordPress homepage on Hostinger.

## 1. Overview

With the move to Vercel, the frontend React app will be deployed on Vercel, and the subdomain `app.ponder.school` will be managed by Vercel. The main WordPress site on `ponder.school` will remain on Hostinger.

## 2. Setup Steps

### A. DNS Configuration
- Update the DNS record for `app.ponder.school` to point to Vercel. This typically involves setting a CNAME record or using Vercel's provided nameservers in your domain registrar's control panel.

### B. Frontend Code Adjustments
- In `frontend/package.json`, ensure the `homepage` field is set appropriately. For a Vercel deployment at the root, you can either remove the `homepage` field or set it to `https://app.ponder.school`.
- Confirm that React Router is configured for client-side routing without extra base paths.

### C. Vercel Configuration
- In the `frontend` directory, create a file named `vercel.json` with the following content:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

This configuration ensures that all routes correctly serve the `index.html` file for a Single Page Application.

### D. Vercel Setup
- Connect your repository to Vercel via the Vercel dashboard.
- When setting up the project, choose the `frontend` folder as the project root.
- Configure build settings: typically, the build command is `npm run build` and the output directory is `build`.

## 3. Post-deployment Checks

- Verify that the deployment is successful on Vercel by accessing `https://app.ponder.school` in a browser (use incognito mode or clear your cache).
- Check Vercel's deployment logs to ensure there are no build or routing issues.
- Confirm that the WordPress homepage (`ponder.school`) remains unaffected on Hostinger.

## 4. Troubleshooting

- If you encounter routing issues, double-check the `rewrites` rules in `vercel.json`.
- Review Vercel logs for any build errors or warnings.
- Ensure that the DNS changes for `app.ponder.school` have fully propagated. 