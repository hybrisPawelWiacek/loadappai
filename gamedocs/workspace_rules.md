# LoadApp.AI Workspace Rules

## 1. Document Reference Guide
- When implementing features or user flows → prd20.md
- When designing component interaction or API endpoints → docs/System_architecture_20.md
- When implementing entities, services, or business logic → Domain_Entities_and_Services.md
- When creating or modifying API endpoints → API_Specification.md


## 2. Core Development Principles
- Follow clean architecture from docs/System_architecture_20.md
- Implement domain model as specified in Domain_Entities_and_Services.md
- Use API patterns from API_Specification.md


## 3. Implementation Focus
- Primary reference for features: prd20.md
  - Route planning with empty driving
  - Cost calculations 
  - Offer generation
  - Streamlit UI implementation
  
- Technical structure: System_Architecture.md
  - Frontend (Streamlit)
  - Backend (Flask)
  - Database (SQLite)
  - External services integration

## 4. Code Organization
- Follow domain patterns: Domain_Entities_and_Services.md
  - Entity definitions and validation
  - Service layer implementation
  - Business logic organization
  
- Follow API design: API_Specification.md
  - Endpoint structure
  - Request/response formats
  - Error handling
  - Status codes


## 6. Checklist to prevent common mistakes
Here's a checklist of best practices to prevent such mistakes:

Before Creating Files:
Search for existing implementations using find_by_name
Check project structure using list_dir
Review related files using related_files
Verify correct directory using project conventions
Project Structure Rules:
Domain code goes in src/domain/
API endpoints in src/api/
Infrastructure code in src/infrastructure/
Frontend code in src/frontend/
File Organization Guidelines:
Keep related code in single files when possible
Follow the established module structure
Use init.py for package organization
Place tests in corresponding test directories
Before Implementation:
Review existing implementations
Check for duplicate functionality
Follow the project's architectural patterns
Verify the correct location based on clean architecture


## 7. Testing Best Practices
- Always run tests with `pytest [test_file] -v` command
- Do not use `python -m pytest` or other variations
- Before modifying code:
  1. Run tests to get baseline
  2. Understand what tests are failing and why
  3. Make changes to both implementation and tests in sync
- When tests fail:
  1. Check if failure is due to:
     - Implementation changes (update tests)
     - Test environment setup (fix mocks/fixtures)
     - Actual bugs (ask for approval tofix implementation)
  2. Update both implementation and tests together
  3. Verify all test cases still make sense
- Maintain test coverage above 60%
- Keep test fixtures up to date with implementation

## 8. SQLAlchemy Model Guidelines
- Avoid using reserved names in model definitions:
  - `metadata` (reserved by SQLAlchemy)
  - `query` (reserved by Flask-SQLAlchemy)
  - `session` (reserved by SQLAlchemy)
- Follow model naming conventions:
  - Use PascalCase for model class names
  - Use snake_case for column names
  - Suffix model classes with 'Model' when in infrastructure layer
- Keep models in dedicated files:
  - Base models in `src/infrastructure/models.py`
  - Complex models in separate files under `src/infrastructure/models/`
- Always define explicit table names:
  ```python
  __tablename__ = 'my_table_name'

## 9. Common Pitfalls Prevention
- Database Type Compatibility:
  - ALWAYS check SQLite type compatibility before implementing models
  - Use string representation for UUIDs (Column(String(36)))
  - Store datetimes with timezone info (Column(DateTime(timezone=True)))
  - Use appropriate numeric types (Integer, Float) based on precision needs

- Before Implementation:
  1. Review SQLite type limitations
  2. Check existing type conversion patterns
  3. Test data type handling in isolation
  4. Document any special type handling requirements

- Code Review Checklist:
  1. Verify UUID fields are stored as strings
  2. Confirm datetime fields include timezone info
  3. Check numeric type precision requirements
  4. Validate foreign key type consistency
  5. Test type conversions in both directions

## 10. Database Design Rules
- SQLite Compatibility Requirements:
  - Store UUIDs as strings (TEXT) - SQLite has no native UUID support
  - Use TEXT for datetime fields with explicit timezone information
  - Use INTEGER for boolean values (0/1)
  - Use REAL for floating-point numbers
  - Avoid using complex JSON structures in indexed columns

- Data Type Conversion Rules:
  - Always convert UUIDs to strings before storing
  - Always store datetimes in UTC timezone
  - Always include timezone information in datetime fields
  - Handle boolean values as 0/1 integers in SQLite

- Model Implementation:
  - Use SQLAlchemy Column(String(36)) for UUID fields
  - Use Column(DateTime(timezone=True)) for datetime fields
  - Document all type conversions in model docstrings
  - Add validators for type conversion where needed