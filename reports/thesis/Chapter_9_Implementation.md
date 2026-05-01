# Chapter 9: Component-Level Code Implementation (Code Snippets)

## 9.1 Introduction to the Codebase
To construct a resilient and scalable Identity-First AI architecture, the Miryn codebase was strictly compartmentalized. This chapter provides a component-level analysis of the core implementation details, bridging the theoretical architecture with the actual source code. The following code snippets demonstrate the exact logic running in production.

## 9.2 The FastAPI Orchestration Layer (`miryn/backend`)
The backend is fundamentally responsible for routing, authentication, and orchestrating the synchronous components of the conversational loop. Built on FastAPI, it leverages Python's `asyncio` for non-blocking I/O.

### 9.2.1 The Chat Router and SSE Streaming (`app/api/chat.py`)
To provide a modern, real-time user experience without relying on heavy WebSockets, Miryn uses `StreamingResponse` with `text/event-stream`. 

**Code Snippet 9.1: Server-Sent Events (SSE) Endpoint implementation**
![SSE Implementation](file:///d:/Projects/MirynAI-Production/Miryn-AI/reports/thesis/images/code_sse.png)

## 9.3 Database Migrations and pgvector (`migrations/001_init.sql`)
The database schema relies heavily on `pgvector` to enable vector math directly within SQL queries.

**Code Snippet 9.2: PostgreSQL Schema for the Episodic Memory Vector DB**
![SQL Schema Implementation](file:///d:/Projects/MirynAI-Production/Miryn-AI/reports/thesis/images/code_sql.png)

## 9.4 The Next.js Frontend Presentation (`miryn/frontend`)
The frontend is built with React and Next.js 14 (App Router). It is designed to be highly responsive and visually communicate the internal state of the AI to the user.

### 9.4.1 The Identity Dashboard UI Rendering (`IdentityDashboard.tsx`)
This component represents the core differentiating UX of the platform. Using Tailwind CSS, floats like `openness: 0.8` are converted into dynamic progress bars.

**Code Snippet 9.3: The gradient meter rendering logic in React**
![React Component Implementation](file:///d:/Projects/MirynAI-Production/Miryn-AI/reports/thesis/images/code_react.png)
This specific code maps the JSON array returned by the API into visual `Meter` components that smoothly transition from amber to white, giving the user immediate visual feedback on the AI's internal belief confidence.
