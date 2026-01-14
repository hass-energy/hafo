```prompt
---
description: Update documentation based on code changes in the current branch compared to main
---

# Update Documentation Based on Branch Changes

Analyze the differences between the current branch and the `main` branch, then update the relevant documentation to reflect all code changes.

## Step 1: Analyze Git Changes

First, identify what has changed:

1. **Get the diff**: Compare the current branch to `main` using `git diff origin/main...HEAD` or `git diff origin/main HEAD`

2. **Categorize changes**:

    - New features (new files, new functions, new classes)
    - Modified features (changed behavior, updated APIs)
    - Deleted features (removed functionality)
    - Bug fixes (behavior corrections)
    - Refactoring (internal changes without behavior changes)

3. **Map changes to documentation areas**:

    - **User-facing changes** → `docs/` (configuration, usage, examples)
    - **Developer-facing changes** → Documentation about architecture and APIs

## Step 2: Documentation Update Strategy

For each identified change, determine what documentation needs updating:

### New Features

- **New forecasting capabilities**: Document configuration and usage
- **New configuration options**: Update relevant documentation pages
- **New sensors**: Document sensor output and behavior

### Modified Features

- **Changed behavior**: Update all documentation that describes the old behavior
- **New parameters**: Add to configuration documentation with examples
- **Deprecated features**: Note deprecation and migration path
- **API changes**: Update developer documentation

### Deleted Features

- **Removed functionality**: Remove or mark as deprecated in documentation
- **Breaking changes**: Document migration path and rationale

## Step 3: Follow Documentation Guidelines

When updating documentation, follow these principles:

### Core Principles

- **Minimalism first**: Keep explanations short and purposeful
- **Match audience**: User docs for UI tasks, developer docs for architecture
- **Link to Home Assistant**: Reference [HA developer docs](https://developers.home-assistant.io/) for standard concepts
- **No unverified claims**: Avoid quantitative performance statements without benchmarks

### Formatting Requirements

- **Semantic line breaks**: One sentence per line, optional breaks at clause boundaries
- **Sentence case**: All headings use sentence case
- **American English**: Use American spelling throughout
- **Backticks**: Use for file paths, filenames, variable names, field entries

### DRY Principle

- **Link, don't duplicate**: Reference existing authoritative sources rather than repeating information
- **Single source of truth**: Maintain one authoritative location for each concept
- **Progressive disclosure**: High-level pages describe patterns, detail pages provide specifics

## Step 4: Consistency Checks

Before finalizing documentation updates:

- [ ] **Terminology**: Verify consistent terminology usage
- [ ] **Links**: Test all internal links resolve correctly
- [ ] **Cross-references**: Update links to changed sections
- [ ] **Formatting**: Ensure semantic line breaks and proper markdown structure

## Step 5: Update Process

1. **Read existing docs**: Understand current documentation structure and style
2. **Identify gaps**: Determine what's missing or outdated
3. **Update systematically**: Work through each affected documentation area
4. **Maintain consistency**: Follow existing patterns and conventions
5. **Verify links**: Check that all internal and external links work
6. **Review formatting**: Ensure semantic line breaks and proper markdown structure

## Output

Provide a summary of:

- Files changed in the branch
- Documentation files updated
- New documentation files created (if any)
- Key changes made to each documentation file
- Any documentation that may need manual review

Focus on accuracy, consistency, and adherence to HAFO documentation standards.

```
