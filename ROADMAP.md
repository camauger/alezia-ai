# Project Improvement Roadmap

This document outlines the steps to improve the Alezia AI codebase, based on the suggestions in `IMPROVEMENTS.md`. The tasks are organized in a logical order, starting with the most critical changes.

## Phase 1: Security and Foundations

These tasks are critical for the security and stability of the application and should be addressed first.

- [x] **Implement a Proper Database Management System:** Replace the custom `db_manager` with SQLAlchemy for all database interactions. This is a foundational change that will affect many other parts of the application.
- [x] **Use Parameterized Queries:** Eliminate all f-string-based queries and use parameterized queries to prevent SQL injection vulnerabilities. This should be done as part of the SQLAlchemy migration.
- [x] **Avoid Hardcoding Secrets:** Move all secrets and security-related configurations to environment variables.

## Phase 2: Performance and Code Quality

These tasks will improve the application's performance, scalability, and code quality.

- [ ] **Use Asynchronous Database Operations:** Migrate all database operations to be asynchronous using a library like `aiosqlite`.
- [x] **Optimize Embedding Loading:** Refactor the `MemoryManager` to load the embedding model as a singleton.
- [x] **Use `Enum` for Memory and Trait Types:** Replace hardcoded string lists with `Enum` for better type safety and maintainability.
- [x] **Consolidate API Client Classes:** Merge the `AleziaAPI` and `MemoryAPI` classes in the frontend to reduce code duplication.

## Phase 3: Testing and Maintainability

These tasks will improve the long-term maintainability of the project.

- [x] **Add Unit and Integration Tests:** Create a comprehensive test suite to ensure the code's correctness and prevent regressions.
- [x] **Use a Linter and Formatter:** Set up a linter and formatter to enforce a consistent code style across the project.