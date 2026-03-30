# B2B Warehouse Management System
B2B warehouse management system for inventory, purchase orders, GRNs, suppliers, and operations dashboards.

## Overview
B2B Warehouse Management System is a codebase focused on delivering the workflows and services represented in this repository. It combines the project modules found in the source tree into a single implementation for development, testing, and deployment. The repository is organized to support maintainable product development with clear separation between application layers and supporting assets.

## Tech Stack
- Alembic
- Docker
- Docker Compose
- FastAPI
- Node.js
- Pytest
- Python
- React
- SQLAlchemy
- TanStack Query
- Temporal
- TypeScript
- Uvicorn
- Vite
- Zustand

## Features
- Supports A Dm In
- Supports B Ac Ko Rd Er S
- Supports D As Hb Oa Rd
- Supports G Rn S
- Supports H Ea Lt H
- Supports P Ro Du Ct S

## Getting Started
### Prerequisites
Node.js 18+
pnpm
Python 3.10+
Docker

### Installation
Run `pnpm install` in each package that contains a `package.json`.
Create a virtual environment and install dependencies from `requirements.txt` or `pyproject.toml`.

### Environment Variables
Copy .env.example to .env and provide the values required for your local environment before starting the application.

### Running the Project
Use `pnpm dev` in the frontend package and any related workspace package.
Start Python API services with the project-specific `uvicorn`, `fastapi`, or package run command.
Use `docker compose up --build` when containerized services are provided.

## Project Structure
- Catchup-Mohith-main/
- .env
- .env.example
- .gitignore

## License
MIT
