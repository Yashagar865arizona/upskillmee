# Frontend

## Project Overview

This is a React-based frontend for a web application. It uses Create React App as a foundation and includes the following key technologies:

*   **React:** For building the user interface.
*   **React Router:** For handling client-side routing.
*   **Redux:** For state management.
*   **Axios:** For making API requests to the backend.
*   **WebSocket:** For real-time communication.



The application features a dashboard, chat functionality, project management, and user authentication. The code is structured into components, pages, and API services.

## Building and Running

### Prerequisites

*   Node.js and npm (or yarn)

### Development

To run the application in development mode:

```bash
npm start
```

This will start a development server on `http://localhost:3000`.

### Testing

To run the test suite:

```bash
npm test
```

### Production

To build the application for production:

```bash
npm run build
```

This will create a `build` directory with the optimized and minified application code.

## Development Conventions

*   **Styling:** The project uses CSS Modules for component-level styling.
*   **API Interaction:** API requests are centralized in the `src/api` directory. Configuration for the API endpoints is in `src/config.js`.
*   **State Management:** Redux is used for global state management.
*   **Routing:** Client-side routing is handled by `react-router-dom`. The main routes are defined in `src/App.js`.
