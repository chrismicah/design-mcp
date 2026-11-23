# Generate UI Blueprint

Before writing ANY code, follow this process:

## Step 1: Research
Use `search_design_patterns` to find 3-5 real-world examples of the requested UI.
Use `get_behavioral_pattern` for any UX patterns involved (empty states, forms, etc.).
Use `get_semantic_tokens` for the styling foundation.

## Step 2: Synthesize
From the examples, identify:
- The most common layout strategy (use this unless the user specifies otherwise)
- Shared UI elements across examples (these are "expected" by users)
- Behavioral patterns (loading, error, empty states)
- Accessibility requirements

## Step 3: Blueprint
Before coding, write a brief blueprint:
- Layout: [type] with [structure description]
- Components: [list of components with key props]
- Behavior: [interaction logic for each state]
- Tokens: [key semantic tokens to use]
- Accessibility: [ARIA roles, contrast requirements, keyboard navigation]

## Step 4: Implement
Now generate the code, using the blueprint as your specification.
Use semantic tokens instead of hardcoded values.
Include all behavioral states (loading, empty, error).
Ensure WCAG AA compliance.
