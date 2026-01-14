````prompt
---
description: Check code coverage and identify untested code that needs test cases
---

# Code Coverage Analysis

Check code coverage for the current branch and identify areas that need additional test cases.

## Step 1: Run Coverage Analysis

### Full Coverage Report

```bash
uv run pytest --cov=custom_components/hafo --cov-branch --cov-report=term-missing
```

This provides:

- Overall coverage percentage
- Branch coverage
- Line-by-line coverage with missing lines identified

### HTML Coverage Report

For detailed visual analysis:

```bash
uv run pytest --cov=custom_components/hafo --cov-branch --cov-report=html
```

Open `htmlcov/index.html` in a browser to see:

- File-by-file coverage
- Line-by-line highlighting
- Branch coverage visualization

### Coverage for Changed Files Only

To focus on changes in the current branch:

```bash
# List changed test files
git diff main...HEAD --name-only -z --diff-filter=AM -- 'tests/**/*.py' | xargs -0 -n1

# Run coverage for changed test files only (safe from shell injection)
git diff main...HEAD --name-only -z --diff-filter=AM -- 'tests/**/*.py' | \
    xargs -0 uv run pytest --cov=custom_components/hafo --cov-branch --cov-report=term-missing
```

## Step 2: Analyze Coverage Results

### Coverage Requirements

- **CI Requirement**: Coverage should be maintained or improved
- **Codecov Enforcement**: Coverage must not decrease from main on changed lines
- **Focus**: Test behavior and edge cases, not arbitrary percentages

### Identify Missing Coverage

For each file with low coverage:

1. **Review untested lines**: Check which lines are not covered

2. **Consider simplification first**: Before adding test cases, evaluate if the code can be simplified:

    - **Simplify logic**: If possible, refactor to remove unnecessary branches and conditional paths
    - **Reduce complexity**: Simpler code with fewer branches is easier to test and maintain
    - **Prefer simplification over testing**: Removing code that needs testing is better than adding tests for complex logic

3. **Determine if coverage is needed**:

    - **Unreachable code**: If lines cannot be covered by exercising input data, they may be unreachable and should be removed
    - **Edge cases**: Missing coverage often indicates untested edge cases
    - **Error paths**: Ensure error handling is tested
    - **Branch coverage**: Check that both true/false branches of conditionals are tested

4. **Prioritize by importance**:

    - Critical business logic (forecasting algorithms, data processing)
    - Error handling paths
    - Edge cases and boundary conditions
    - New features added in this branch

## Step 3: Add Test Cases

### Test Style Guidelines

Follow HAFO testing standards from `.github/instructions/tests.instructions.md`:

- **Function-style tests**: Use `def test_...()` not class-based tests
- **Parametrized tests**: Use `@pytest.mark.parametrize` for data-driven tests
- **Direct property access**: Access properties directly without None checks when you've created the entities

### Where to Add Tests

1. **Forecaster logic**: Add tests to `tests/` for forecasting functionality
2. **Config flows**: Add tests for configuration flow handling
3. **Coordinator**: Add tests for data coordination and updates
4. **New functionality**: Create appropriate test files following existing patterns

## Step 4: Verify Coverage Improvement

After adding tests:

1. **Re-run coverage**:

    ```bash
    uv run pytest --cov=custom_components/hafo --cov-branch --cov-report=term-missing
    ```

2. **Check coverage for changed lines**:

    - Ensure new code has adequate coverage
    - Verify coverage hasn't decreased for modified code

3. **Run tests to ensure they pass**:

    ```bash
    uv run pytest
    ```

## Step 5: Summary

Provide a summary of:

- Current overall coverage percentage
- Coverage for changed files (if applicable)
- Files with low coverage that need attention
- Test cases added to improve coverage
- Any unreachable code identified
- Confirmation that coverage requirements are met

## Notes

- **Coverage philosophy**: Focus on testing behavior and edge cases, not achieving arbitrary percentages
- **Simplification preferred**: When encountering untested code, first consider if the logic can be simplified to remove branches and lines that need testing
- **Codecov**: Enforces that coverage does not decrease from main on changed lines
- **Unreachable code**: If lines cannot be covered by exercising input data, they may be unreachable and should be removed
- **Branch coverage**: Use `--cov-branch` to ensure both branches of conditionals are tested

````
