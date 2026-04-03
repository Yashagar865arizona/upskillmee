import React from 'react';
import styles from './ErrorBoundary.module.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null,
      retryCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { 
      hasError: true,
      errorId: Date.now().toString(36) + Math.random().toString(36).substr(2)
    };
  }

  componentDidCatch(error, errorInfo) {
    // Log error details
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Update state with error details
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // In production, you would send this to an error reporting service
    if (process.env.NODE_ENV === 'production') {
      // Example: Send to error reporting service
      // errorReportingService.captureException(error, {
      //   extra: errorInfo,
      //   tags: { component: 'ErrorBoundary' }
      // });
    }
  }

  handleRetry = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null,
      retryCount: this.state.retryCount + 1
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      const { fallback: CustomFallback, level = 'page' } = this.props;
      
      if (CustomFallback) {
        return (
          <CustomFallback
            error={this.state.error}
            errorInfo={this.state.errorInfo}
            onRetry={this.handleRetry}
            onReload={this.handleReload}
          />
        );
      }

      // Default fallback UI based on error level
      if (level === 'component') {
        return (
          <div className={styles.componentError}>
            <div className={styles.errorIcon}>⚠️</div>
            <div className={styles.errorContent}>
              <h3>Something went wrong</h3>
              <p>This component encountered an error and couldn't load properly.</p>
              {this.state.retryCount < 3 && (
                <button 
                  onClick={this.handleRetry}
                  className={styles.retryButton}
                  aria-label="Retry loading component"
                >
                  Try Again
                </button>
              )}
              {this.state.retryCount >= 3 && (
                <p className={styles.maxRetriesText}>
                  Maximum retry attempts reached. Please refresh the page.
                </p>
              )}
            </div>
          </div>
        );
      }

      // Page-level error
      return (
        <div className={styles.pageError}>
          <div className={styles.errorContainer}>
            <div className={styles.errorIcon}>🚨</div>
            <h1>Oops! Something went wrong</h1>
            <p className={styles.errorMessage}>
              We're sorry, but something unexpected happened. Our team has been notified.
            </p>
            
            <div className={styles.errorActions}>
              <button 
                onClick={this.handleRetry}
                className={styles.primaryButton}
              >
                Try Again
              </button>
              <button 
                onClick={this.handleReload}
                className={styles.secondaryButton}
              >
                Reload Page
              </button>
            </div>

            {process.env.NODE_ENV === 'development' && (
              <details className={styles.errorDetails}>
                <summary>Error Details (Development Only)</summary>
                <div className={styles.errorStack}>
                  <h4>Error:</h4>
                  <pre>{this.state.error && this.state.error.toString()}</pre>
                  
                  <h4>Component Stack:</h4>
                  <pre>{this.state.errorInfo.componentStack}</pre>
                  
                  <h4>Error ID:</h4>
                  <code>{this.state.errorId}</code>
                </div>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;