# Global AI Rules for Development

## 1. Development Environment & Dependencies
- Always use Python virtual environment (venv)
- Maintain updated requirements.txt with explicit versions
- Separate dev dependencies into requirements-dev.txt
- Use .env files for environment variables
- Keep .gitignore updated with environment files

## 2. Version Control & Commits
- Create atomic commits for completed and approved features
- Use conventional commit messages:
  - feat: new features
  - fix: bug fixes
  - docs: documentation changes
  - refactor: code restructuring
- Include relevant ticket/issue numbers
- Add brief descriptions of significant changes
- Create commits only after explicit approval

## 3. Port Usage & Service Configuration
- NEVER use port 5000 for any backend services (conflicts with Apple AirTunes)
- Default ports:
  - Backend (Flask): 5001
  - Frontend (Streamlit): 8501
- Always check for port conflicts before starting services
- Log port configuration in startup messages

## 4. Architectural Philosophy
- Prefer simplicity over complexity
- Avoid premature optimization
- Follow YAGNI (You Aren't Gonna Need It) principle
- However, maintain:
  - Clean architecture principles
  - Domain-driven design practices
  - Clear separation of concerns
  - Proper error handling
  - Essential documentation

## 4. Clean Architecture Principles
- Separate domain logic from infrastructure
- Use dataclasses for domain entities
- Keep services stateless and focused
- Follow dependency injection patterns
- Document public interfaces and domain logic

## 5. Code Style & Documentation
- Use Python type hints consistently
- Follow Google-style docstrings
- Group imports: standard lib, third-party, local
- Include meaningful commit messages
- Add TODO markers for future extension points

## 6. Code Safety & Change Management
- Never modify working, approved code without explicit permission
- Request approval before modifying code outside current task scope
- When suggesting changes to existing code:
  1. Explain why the change is needed
  2. Show which files would be affected
  3. Wait for explicit approval before proceeding
- Focus changes only on files directly related to current task
- Flag any potential impacts on existing functionality

## 7. Testing Discipline
- Run full test suite after each implementation
- When tests fail:
  1. Analyze cause of failure
  2. Present two options with pros/cons:
     a) Update tests to match new requirements
     b) Modify code to make tests pass
  3. Wait for explicit decision before proceeding
- Document any test modifications with rationale
- Ensure test coverage for new functionality
- Maintain existing test integrity

## 8. Development Workflow
- Start with minimal viable solution
- Create implementation artifacts for major tasks:
  1. "Gameplan" document outlining:
     - Step-by-step implementation approach
     - Key technical decisions and trade-offs
     - Integration points and dependencies
     - Potential risks and mitigations
  2. "Implementation Checklist" tracking:
     - Core functionality components
     - Required tests and validations
     - Documentation updates
     - Integration verification steps
- Track progress against the checklist
- Reference gameplan during implementation
- Suggest iterative improvements
- Comment on potential optimizations
- Reference relevant documentation
- Highlight technical risks
