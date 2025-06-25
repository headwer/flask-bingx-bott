# TradingView → BingX Webhook System

## Overview

This is a Flask-based webhook system that receives trading signals from TradingView and automatically executes trades on the BingX exchange. The application provides a web interface for monitoring system status and testing webhook functionality.

## System Architecture

The system follows a simple three-tier architecture:

1. **Presentation Layer**: Flask web application with HTML templates
2. **Business Logic Layer**: Webhook processing and trade execution logic
3. **Integration Layer**: BingX API client for exchange communication

### Technology Stack
- **Backend**: Python 3.11 with Flask framework
- **HTTP Server**: Gunicorn for production deployment
- **API Integration**: BingX REST API
- **Frontend**: Bootstrap 5 with dark theme
- **Package Management**: UV lock file system

## Key Components

### Core Application (`app.py`)
- Flask web server setup
- Webhook endpoint (`/webhook`) for receiving TradingView signals
- Dashboard routes for monitoring and testing
- Request validation and error handling
- Session management with configurable secret key

### Webhook Handler (`webhook_handler.py`)
- Processes incoming TradingView signals
- Validates trade parameters (action, ticker, quantity)
- Orchestrates trade execution through BingX client
- Error handling and response formatting

### BingX API Client (`bingx_client.py`)
- Authenticated API communication with BingX exchange
- HMAC-SHA256 signature generation for secure requests
- Trade execution methods (incomplete in current implementation)
- Connection testing capabilities

### Web Interface
- **Dashboard** (`templates/index.html`): System status monitoring
- **Test Interface** (`templates/test_webhook.html`): Manual webhook testing
- **Styling** (`static/style.css`): Custom CSS for enhanced UI

## Data Flow

1. **Signal Reception**: TradingView sends POST request to `/webhook` endpoint
2. **Validation**: System validates JSON payload for required fields (`accion`, `ticker`, `balance`)
3. **Processing**: WebhookHandler processes the signal and determines trade parameters
4. **Execution**: BingXClient executes the trade on the exchange
5. **Response**: System returns success/error status to TradingView

### Required Webhook Payload Format
```json
{
  "accion": "BUY" | "SELL",
  "ticker": "trading-pair",
  "balance": number
}
```

## External Dependencies

### Environment Variables
- `BINGX_API_KEY`: BingX API key for authentication
- `BINGX_SECRET_KEY`: BingX secret key for signature generation
- `SESSION_SECRET`: Flask session secret (optional, defaults to dev key)

### Third-Party Services
- **BingX Exchange**: Primary trading platform integration
- **TradingView**: Signal source for automated trading

### Python Dependencies
- `flask`: Web framework and routing
- `requests`: HTTP client for API calls
- `gunicorn`: WSGI HTTP server for production
- `psycopg2-binary`: PostgreSQL adapter (available but not currently used)
- `email-validator`: Email validation utilities

## Deployment Strategy

### Replit Configuration
- **Runtime**: Python 3.11 with Nix package management
- **Packages**: OpenSSL and PostgreSQL system packages
- **Deployment Target**: Autoscale deployment on Replit
- **Port Configuration**: Application runs on port 5000

### Production Server
- **WSGI Server**: Gunicorn with bind to `0.0.0.0:5000`
- **Process Management**: Reusable ports with reload capability
- **Workflow**: Parallel task execution for development

### Security Considerations
- API credentials stored as environment variables
- HMAC-SHA256 signature validation for BingX API
- JSON-only webhook endpoint with content-type validation
- Session secret configuration for Flask security

## Changelog
```
Changelog:
- June 25, 2025. Initial setup
```

## User Preferences

Preferred communication style: Simple, everyday language.

## Notes for Development

### Current Implementation Status
- ✅ Webhook endpoint with validation
- ✅ BingX API client structure
- ✅ Web interface for monitoring
- ⚠️ Trade execution methods incomplete in BingXClient
- ⚠️ Database integration available but not implemented
- ⚠️ Test connection method referenced but not implemented

### Architectural Decisions

**Flask over FastAPI**: Chosen for simplicity and extensive ecosystem support for webhook applications.

**BingX Integration**: Selected as the primary exchange due to API accessibility and trading features.

**Environment-based Configuration**: Keeps sensitive credentials secure while allowing easy deployment configuration.

**Bootstrap Dark Theme**: Provides professional appearance suitable for trading applications while maintaining accessibility.

**Gunicorn Deployment**: Robust WSGI server choice for production Flask applications with autoscaling capabilities.