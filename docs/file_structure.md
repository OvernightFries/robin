# File Structure Documentation

## Project Overview
This document provides a detailed description of every file in the Robin AI project, organized by directory structure.

## Root Directory

### `README.md`
- **Purpose**: Main project documentation
- **Contents**: 
  - Project overview
  - Architecture description
  - Technical stack details
  - Setup instructions
  - API documentation
  - Development guide
  - Deployment instructions
  - Troubleshooting guide
  - Contributing guidelines

### `docker-compose.yml`
- **Purpose**: Docker container orchestration
- **Contents**:
  - Service definitions for frontend, backend, and AI services
  - Network configurations
  - Volume mappings
  - Environment variables
  - Health checks
  - Port mappings

## Frontend (`src/`)

### `src/app/page.tsx`
- **Purpose**: Main application page
- **Contents**:
  - React component for the home page
  - Stock symbol input form
  - Analyze button implementation
  - Navigation logic
  - State management for user input

### `src/app/analyze/[symbol]/page.tsx`
- **Purpose**: Stock analysis page
- **Contents**:
  - Dynamic route for stock symbols
  - Chat interface component
  - Real-time market data display
  - WebSocket connection handling
  - Message processing logic

### `src/app/globals.css`
- **Purpose**: Global styles
- **Contents**:
  - Tailwind CSS configurations
  - Custom component styles
  - Color schemes
  - Responsive design utilities
  - Animation definitions

### `src/app/layout.tsx`
- **Purpose**: Root layout component
- **Contents**:
  - HTML structure
  - Metadata configuration
  - Global providers
  - Navigation components
  - Theme setup

## Backend (`backend/`)

### `backend/main.py`
- **Purpose**: FastAPI application entry point
- **Contents**:
  - API route definitions
  - WebSocket server setup
  - Middleware configurations
  - Error handlers
  - Health check endpoints

### `backend/rag/pdf_cleaner.py`
- **Purpose**: PDF processing and text extraction
- **Contents**:
  - PDF text extraction methods
  - Text cleaning utilities
  - Chunking logic
  - Embedding generation
  - Vector store integration

### `backend/rag/process_pdfs.py`
- **Purpose**: PDF processing script
- **Contents**:
  - Batch processing logic
  - File system operations
  - Progress tracking
  - Error handling
  - Logging configuration

### `backend/requirements.txt`
- **Purpose**: Python dependencies
- **Contents**:
  - FastAPI
  - PyPDF2
  - Pinecone client
  - Redis client
  - Other required packages

## Documentation (`docs/`)

### `docs/backend.md`
- **Purpose**: Backend system documentation
- **Contents**:
  - Architecture details
  - API specifications
  - Data models
  - System components
  - Performance optimization
  - Security measures
  - Deployment guidelines

### `docs/frontend.md`
- **Purpose**: Frontend system documentation
- **Contents**:
  - Component architecture
  - State management
  - UI/UX guidelines
  - Performance optimization
  - Testing strategies
  - Deployment process

### `docs/file_structure.md`
- **Purpose**: File structure documentation
- **Contents**:
  - Directory organization
  - File descriptions
  - Purpose of each file
  - Dependencies
  - Usage guidelines

## Configuration Files

### `.env`
- **Purpose**: Environment variables
- **Contents**:
  - API keys
  - Service URLs
  - Database credentials
  - Feature flags
  - Environment-specific settings

### `.gitignore`
- **Purpose**: Git ignore rules
- **Contents**:
  - Node modules
  - Python virtual environments
  - Environment files
  - Build artifacts
  - Log files

### `package.json`
- **Purpose**: Node.js project configuration
- **Contents**:
  - Dependencies
  - Scripts
  - Project metadata
  - Build configurations
  - Development tools

### `tsconfig.json`
- **Purpose**: TypeScript configuration
- **Contents**:
  - Compiler options
  - Module resolution
  - Type checking rules
  - Path aliases
  - Build settings

## Data Directory (`backend/data/`)

### `backend/data/docs/`
- **Purpose**: Document storage
- **Contents**:
  - PDF files for RAG system
  - Processed text files
  - Metadata files
  - Vector embeddings

### `backend/data/logs/`
- **Purpose**: Log storage
- **Contents**:
  - Application logs
  - Error logs
  - Access logs
  - Performance metrics

## Test Directory (`tests/`)

### `tests/frontend/`
- **Purpose**: Frontend tests
- **Contents**:
  - Component tests
  - Integration tests
  - UI tests
  - Performance tests

### `tests/backend/`
- **Purpose**: Backend tests
- **Contents**:
  - API tests
  - Service tests
  - Database tests
  - Integration tests

## Build Files

### `Dockerfile`
- **Purpose**: Frontend container definition
- **Contents**:
  - Base image
  - Build steps
  - Dependencies
  - Environment setup
  - Entry point

### `backend/Dockerfile`
- **Purpose**: Backend container definition
- **Contents**:
  - Python environment
  - Dependencies
  - Application setup
  - Health checks
  - Entry point 
