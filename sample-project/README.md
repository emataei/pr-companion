# Sample Next.js Project

This is a sample Next.js + TypeScript project designed to test the code quality gate system and PR visual generation workflow. The project demonstrates modern React patterns and best practices.

## Features

- **Health Monitoring**: Real-time system health dashboard with comprehensive API endpoint
- **User Management**: User profile components with form handling, validation, and edit capabilities
- **API Integration**: RESTful endpoints with proper error handling and response formatting
- **TypeScript Safety**: Comprehensive type definitions and interfaces with strict type checking
- **PR Visuals**: Automated generation of impact heatmaps and development flow charts
- **Component Library**: Reusable components following accessibility guidelines

## API Endpoints

### Health Check
- `GET /api/health` - Returns comprehensive system status
- Response includes: status, timestamp, version, uptime, environment, memory usage, service status
- Enhanced monitoring with memory statistics and service health checks

### User Management  
- `GET /api/users` - List all users with pagination
- `GET /api/users/[id]` - Get specific user details with preferences
- `PUT /api/users/[id]` - Update user information and settings
- New: User preferences support (theme, notifications, language)

## Purpose

This project contains intentional code quality issues to demonstrate:

- **Security Issues**: Hardcoded secrets, SQL injection vulnerabilities
- **Type Safety Issues**: Missing TypeScript annotations, `any` types
- **Code Quality Issues**: Complex functions, missing error handling
- **Best Practice Violations**: Debug logs, unused imports
- **Good Examples**: Components that follow Copilot instructions

## Files Overview

- `src/app/page.tsx` - Contains multiple quality issues for testing
- `src/app/api/users/route.ts` - API route with security vulnerabilities
- `src/components/UserProfile.tsx` - Example of good code following standards
- `src/app/layout.tsx` - Basic layout with some TypeScript issues

## Testing the Quality Gate

This project is designed to trigger various levels of quality gate responses:

1. **Blocking Issues**: Security vulnerabilities that prevent merge
2. **Warning Issues**: Quality improvements that should be addressed
3. **Advisory Issues**: Suggestions for better code

The quality gate should detect and report these issues with actionable suggestions based on the project's Copilot instructions.
