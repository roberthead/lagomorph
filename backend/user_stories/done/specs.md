# User Story: Test Coverage for Backend API

## Context

This application is evolving from a web scraping tool into a general-purpose agentic AI framework. We need comprehensive test coverage to ensure reliability as the architecture changes.

## User Story

AS a developer working on the agentic framework
WHEN I run the test suite
I WANT to see test results with coverage metrics
SO THAT I can ensure the core framework components are well-tested and safe to refactor

## Acceptance Criteria

- [x] Test coverage is measured and reported for the backend
- [x] Overall test coverage is at least 80% for the backend codebase (achieved 87%)
- [x] Coverage report is generated in HTML format for easy review
- [x] Coverage command is documented in README.md
- [x] Tests cover the following critical areas:
  - [x] Agent orchestration logic (ChatAgent, ScrapingAgent) - 97-99% coverage
  - [x] Database models and relationships - 100% coverage
  - [x] API endpoints (basic happy path and error cases) - 57-74% coverage
  - [x] Validation framework (BaseValidator, AddressCompletenessValidator) - 91-93% coverage

## Implementation Guidance
- Use pytest with pytest-cov for coverage measurement
- Focus on unit tests for services and models
- Add integration tests for API endpoints
- Exclude migrations and venv from coverage calculation
- Add coverage badge/report to CI/CD if GitHub Actions exists

## Out of Scope (for this story)
- Frontend testing (separate story)
- End-to-end testing
- Performance testing
- 100% coverage requirement (80% is sufficient)

## Definition of Done
- Tests can be run with a single command (e.g., `pytest --cov`)
- Coverage report shows >= 80% overall backend coverage
- README updated with testing instructions
- All tests pass in CI (if applicable)

## Notes
- This establishes baseline test coverage before refactoring toward general-purpose agent framework
- Consider parameterized tests for validators (extensibility pattern)
- Agent prompt behavior should be tested with mocked database calls
