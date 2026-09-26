### Prompt
/init

---

**Status:** active  **Date:** 2026-09-26

---

### 👤 User

<task>
Please analyze this codebase and create an AGENTS.md file containing:
1. Build/lint/test commands - especially for running a single test
2. Code style guidelines including imports, formatting, types, naming conventions, error handling, etc.
</task>

<initialization>
  <purpose>
    Create (or update) a concise AGENTS.md file that enables immediate productivity for AI assistants.
    Focus ONLY on project-specific, non-obvious information that you had to discover by reading files.

    CRITICAL: Only include information that is:
    - Non-obvious (couldn't be guessed from standard practices)
    - Project-specific (not generic to the framework/language)
    - Discovered by reading files (config files, code patterns, custom utilities)
    - Essential for avoiding mistakes or following project conventions

    Usage notes:
    - The file you create will be given to agentic coding agents (such as yourself) that operate in this repository
    - Keep the main AGENTS.md concise - aim for about 20 lines, but use more if the project complexity requires it
    - If there's already an AGENTS.md, improve it
    - If there are Claude Code rules (in CLAUDE.md), Cursor rules (in .cursor/rules/ or .cursorrules), or Copilot rules (in .github/copilot-instructions.md), make sure to include them
    - Be sure to prefix the file with: "# AGENTS.md\n\nThis file provides guidance to agents when working with code in this repository."
  </purpose>

  <todo_list_creation>
    If the update_todo_list tool is available, create a todo list with these focused analysis steps:

    1. Check for existing AGENTS.md files
       CRITICAL - Check these EXACT paths IN THE PROJECT ROOT:
       - AGENTS.md (in project root directory)
       - .bob/rules-agent/AGENTS.md (relative to project root)
       - .bob/rules-ask/AGENTS.md (relative to project root)
       - .bob/rules-plan/AGENTS.md (relative to project root)

       IMPORTANT: All paths are relative to the project/workspace root, NOT system root!

       If ANY of these exist:
       - Read them thoroughly
       - CRITICALLY EVALUATE: Remove ALL obvious information
       - DELETE entries that are standard practice or framework defaults
       - REMOVE anything that could be guessed without reading files
       - Only KEEP truly non-obvious, project-specific discoveries
       - Then add any new non-obvious patterns you discover

       Also check for other AI assistant rules:
       - .cursorrules, CLAUDE.md, .roorules
       - .cursor/rules/, .github/copilot-instructions.md

    2. Identify stack
       - Language, framework, build tools
       - Package manager and dependencies

    3. Extract commands
       - Build, test, lint, run
       - Critical directory-specific commands

    4. Map core architecture
       - Main components and flow
       - Key entry points

    5. Document critical patterns
       - Project-specific utilities (that you discovered by reading code)
       - Non-standard approaches (that differ from typical patterns)
       - Custom conventions (that aren't obvious from file structure)

    6. Extract code style
       - From config files only
       - Key conventions

    7. Testing specifics
       - Framework and run commands
       - Directory requirements

    8. Compile/Update AGENTS.md files
       - If files exist: AGGRESSIVELY clean them up
         * DELETE all obvious information (even if it was there before)
         * REMOVE standard practices, framework defaults, common patterns
         * STRIP OUT anything derivable from file structure or names
         * ONLY KEEP truly non-obvious discoveries
         * Then add newly discovered non-obvious patterns
         * Result should be SHORTER and MORE FOCUSED than before
       - If creating new: Follow the non-obvious-only principle
       - Create mode-specific files in .bob/rules-*/ directories (IN PROJECT ROOT)

    Note: If update_todo_list is not available, proceed with the analysis workflow directly without creating a todo list.
  </todo_list_creation>
</initialization>

<analysis_workflow>
  Follow the comprehensive analysis workflow to:

  1. **Discovery Phase**:
     CRITICAL - First check for existing AGENTS.md files at these EXACT locations IN PROJECT ROOT:
     - AGENTS.md (in project/workspace root)
     - .bob/rules-agent/AGENTS.md (relative to project root)
     - .bob/rules-ask/AGENTS.md (relative to project root)
     - .bob/rules-plan/AGENTS.md (relative to project root)

     IMPORTANT: The .bob folder should be created in the PROJECT ROOT, not system root!

     If found, perform CRITICAL analysis:
     - What information is OBVIOUS and must be DELETED?
     - What violates the non-obvious-only principle?
     - What would an experienced developer already know?
     - DELETE first, then consider what to add
     - The file should get SHORTER, not longer

     Also find other AI assistant rules and documentation

  2. **Project Identification**: Identify language, stack, and build system
  3. **Command Extraction**: Extract and verify essential commands
  4. **Architecture Mapping**: Create visual flow diagrams of core processes
  5. **Component Analysis**: Document key components and their interactions
  6. **Pattern Analysis**: Identify project-specific patterns and conventions
  7. **Code Style Extraction**: Extract formatting and naming conventions
  8. **Security & Performance**: Document critical patterns if relevant
  9. **Testing Discovery**: Understand testing setup and practices
  10. **Example Extraction**: Find real examples from the codebase
</analysis_workflow>

<output_structure>
  <main_file>
    Create or deeply improve AGENTS.md with ONLY non-obvious information:

    If AGENTS.md exists:
    - FIRST: Delete ALL obvious information
    - REMOVE: Standard commands, framework defaults, common patterns
    - STRIP: Anything that doesn't require file reading to know
    - EVALUATE: Each line - would an experienced dev be surprised?
    - If not surprised, DELETE IT
    - THEN: Add only truly non-obvious new discoveries
    - Goal: File should be SHORTER and MORE VALUABLE

    Content should include:
    - Header: "# AGENTS.md\n\nThis file provides guidance to agents when working with code in this repository."
    - Build/lint/test commands - ONLY if they differ from standard package.json scripts
    - Code style - ONLY project-specific rules not covered by linter configs
    - Custom utilities or patterns discovered by reading the code
    - Non-standard directory structures or file organizations
    - Project-specific conventions that violate typical practices
    - Critical gotchas that would cause errors if not followed

    EXCLUDE obvious information like:
    - Standard npm/yarn commands visible in package.json
    - Framework defaults (e.g., "React uses JSX")
    - Common patterns (e.g., "tests go in __tests__ folders")
    - Information derivable from file extensions or directory names

    Keep it concise (aim for ~20 lines, but expand as needed for complex projects).
    Include existing AI assistant rules from CLAUDE.md, Cursor rules (.cursor/rules/ or .cursorrules), or Copilot rules (.github/copilot-instructions.md).
  </main_file>

  <mode_specific_files>
    Create or deeply improve mode-specific AGENTS.md files IN THE PROJECT ROOT.

    CRITICAL: For each of these paths (RELATIVE TO PROJECT ROOT), check if the file exists FIRST:
    - .bob/rules-agent/AGENTS.md (relative to project root)
    - .bob/rules-ask/AGENTS.md (relative to project root)
    - .bob/rules-plan/AGENTS.md (relative to project root)

    IMPORTANT: The .bob directory must be created in the current project/workspace root directory,
    NOT at the system root (/) or home directory. All paths are relative to where the project is located.

    If files exist:
    - AGGRESSIVELY DELETE obvious information
    - Remove EVERYTHING that's standard practice
    - Strip out framework defaults and common patterns
    - Each remaining line must be surprising/non-obvious
    - Only then add new non-obvious discoveries
    - Files should become SHORTER, not longer

    Example structure (ALL IN PROJECT ROOT):
    ```
    project-root/
    ├── AGENTS.md                    # General project guidance
    ├── .bob/                        # IN PROJECT ROOT, NOT SYSTEM ROOT!
    │   ├── rules-agent/
    │   │   └── AGENTS.md           # Advance mode specific instructions
    │   ├── rules-ask/
    │   │   └── AGENTS.md           # Ask mode specific instructions
    │   └── rules-plan/
    │       └── AGENTS.md           # Plan mode specific instructions
    ├── src/
    ├── package.json
    └── ... other project files
    ```

    .bob/rules-agent/AGENTS.md - ONLY non-obvious advance coding rules discoveries:
    - Custom utilities that replace standard approaches
    - Non-standard patterns unique to this project
    - Hidden dependencies or coupling between components
    - Required import orders or naming conventions not enforced by linters
    - Access to tools like MCP and Browser

    Example of non-obvious rules worth documenting:
    ```
    # Project Coding Rules (Non-Obvious Only)
    - Always use safeWriteJson() from src/utils/ instead of JSON.stringify for file writes (prevents corruption)
    - API retry mechanism in src/api/providers/utils/ is mandatory (not optional as it appears)
    - Database queries MUST use the query builder in packages/evals/src/db/queries/ (raw SQL will fail)
    - Provider interface in packages/types/src/ has undocumented required methods
    - Test files must be in same directory as source for vitest to work (not in separate test folder)
    ```

    .bob/rules-ask/AGENTS.md - ONLY non-obvious documentation context:
    - Hidden or misnamed documentation
    - Counterintuitive code organization
    - Misleading folder names or structures
    - Important context not evident from file structure

    Example of non-obvious documentation rules worth documenting:
    ```
    # Project Documentation Rules (Non-Obvious Only)
    - "src/" contains VSCode extension code, not source for web apps (counterintuitive)
    - Provider examples in src/api/providers/ are the canonical reference (docs are outdated)
    - UI runs in VSCode webview with restrictions (no localStorage, limited APIs)
    - Package.json scripts must be run from specific directories, not root
    - Locales in root are for extension, webview-ui/src/i18n for UI (two separate systems)
    ```

    .bob/rules-plan/AGENTS.md - ONLY non-obvious architectural constraints:
    - Hidden coupling between components
    - Undocumented architectural decisions
    - Non-standard patterns that must be followed
    - Performance bottlenecks discovered through investigation

    Example of non-obvious architecture rules worth documenting:
    ```
    # Project Architecture Rules (Non-Obvious Only)
    - Providers MUST be stateless - hidden caching layer assumes this
    - Webview and extension communicate through specific IPC channel patterns only
    - Database migrations cannot be rolled back - forward-only by design
    - React hooks required because external state libraries break webview isolation
    - Monorepo packages have circular dependency on types package (intentional)
    ```
  </mode_specific_files>
</output_structure>

<quality_criteria>
  - ONLY include non-obvious information discovered by reading files
  - Exclude anything that could be guessed from standard practices
  - Focus on gotchas, hidden requirements, and counterintuitive patterns
  - Include specific file paths when referencing custom utilities
  - Be extremely concise - if it's obvious, don't include it
  - Every line should prevent a potential mistake or confusion
  - Test: Would an experienced developer be surprised by this information?
  - If updating existing files: DELETE obvious info first, files should get SHORTER
  - Measure success: Is the file more concise and valuable than before?
</quality_criteria>

Remember: The goal is to create documentation that enables AI assistants to be immediately productive in this codebase, focusing on project-specific knowledge that isn't obvious from the code structure alone.

---

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[-] Check for existing AGENTS.md files and other AI rules
[ ] Identify stack, language, framework, build tools
[ ] Extract commands (build, test, lint, run)
[ ] Map core architecture and key entry points
[ ] Document critical patterns and code style
[ ] Compile AGENTS.md files


### 🤖 Assistant

> 🔧 called: glob, glob, glob



> 🔧 **glob** — AGENTS.md

> 🔧 **glob** — .bob/rules-*/AGENTS.md

> 🔧 **glob** — {CLAUDE.md,.cursorrules,.roorules,.github/copilot-instructions.md}

### 🤖 Assistant

> 🔧 called: list_files, read_file



> 🔧 **list_files** — .

> 🔧 **read_file** — SPEC.md

### 🤖 Assistant

> 🔧 called: list_files, list_files, read_file



> 🔧 **list_files** — analyzer

> 🔧 **list_files** — redline_bob

> 🔧 **read_file** — manage.py

### 🤖 Assistant

> 🔧 called: list_files, list_files, read_file



> 🔧 **list_files** — analyzer/core

> 🔧 **list_files** — redline_bob/settings

> 🔧 **read_file** — analyzer/tests.py

### 🤖 Assistant

> 🔧 called: read_file, read_file, read_file, read_file



> 🔧 **read_file** — analyzer/core/classifier.py

> 🔧 **read_file** — analyzer/core/paths.py

> 🔧 **read_file** — analyzer/core/parser.py

> 🔧 **read_file** — analyzer/core/report.py

### 🤖 Assistant

> 🔧 called: read_file, read_file, read_file



> 🔧 **read_file** — analyzer/models.py

> 🔧 **read_file** — analyzer/views.py

> 🔧 **read_file** — redline_bob/settings/base.py

### 🤖 Assistant

> 🔧 called: read_file, read_file, read_file



> 🔧 **read_file** — redline_bob/settings/development.py

> 🔧 **read_file** — redline_bob/settings/production.py

> 🔧 **read_file** — redline_bob/urls.py

### 🤖 Assistant

> 🔧 called: read_file, glob, glob



> 🔧 **glob** — requirements*.txt

> 🔧 **glob** — *.cfg

> 🔧 **read_file** — README.md

### 🤖 Assistant

> 🔧 called: glob, glob, list_files



> 🔧 **glob** — *.toml

> 🔧 **glob** — *.ini

> 🔧 **list_files** — venv

### 🤖 Assistant

> 🔧 called: execute_command, list_files



> 🔧 **execute_command** — cat venv/pyvenv.cfg && pip freeze 2>/dev/null || (source venv/bin/activate && pip freeze)

> 🔧 **list_files** — samples

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — source venv/bin/activate 2>/dev/null; pip freeze 2>/dev/null; cat venv/lib/python*/site-packages/django/__init__.py 2>/dev/null | head -5; ls venv/lib/ 2>/dev/null

### 🤖 Assistant

> 🔧 called: list_files, list_files, list_files



> 🔧 **list_files** — bob_sessions

> 🔧 **list_files** — analyzer/migrations

> 🔧 **list_files** — analyzer/templates

### 🤖 Assistant

> 🔧 called: list_files



> 🔧 **list_files** — analyzer/templates/analyzer

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — .gitignore

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Check for existing AGENTS.md files and other AI rules
[x] Identify stack, language, framework, build tools
[x] Extract commands (build, test, lint, run)
[x] Map core architecture and key entry points
[x] Document critical patterns and code style
[-] Compile AGENTS.md files


### 🤖 Assistant

> 🔧 called: write_file

Now I have a clear picture of the project. Let me create the AGENTS.md files.

> 🔧 **write_file** — AGENTS.md

### 🤖 Assistant

> 🔧 called: execute_command

Now create the mode-specific files:

> 🔧 **execute_command** — mkdir -p .bob/rules-agent .bob/rules-ask .bob/rules-plan

### 🤖 Assistant

> 🔧 called: write_file, write_file, write_file



> 🔧 **write_file** — .bob/rules-agent/AGENTS.md

> 🔧 **write_file** — .bob/rules-ask/AGENTS.md

> 🔧 **write_file** — .bob/rules-plan/AGENTS.md

### 🤖 Assistant

> 🔧 called: update_todo_list



> 🔧 **update_todo_list** — 
[x] Check for existing AGENTS.md files and other AI rules
[x] Identify stack, language, framework, build tools
[x] Extract commands (build, test, lint, run)
[x] Map core architecture and key entry points
[x] Document critical patterns and code style
[x] Compile AGENTS.md files


### 🤖 Assistant

Four files created:

**[`AGENTS.md`](AGENTS.md)** — General project guidance covering:
- Stack: Django 6.1 + DRF, Python 3.14, venv-based deps
- Commands: dev server, run all tests, run a single test (`python manage.py test analyzer.tests.Class.method`), migrations
- Non-obvious: settings split, `Asia/Kathmandu` timezone, no `requirements.txt` (venv-only), `SPEC.md` as authoritative spec
- Architecture: the four empty core modules and their intended pipeline roles

**[`.bob/rules-agent/AGENTS.md`](.bob/rules-agent/AGENTS.md)** — Coding-specific gotchas: empty stub modules, where to add URLs, test file location, no requirements.txt trap

**[`.bob/rules-ask/AGENTS.md`](.bob/rules-ask/AGENTS.md)** — Documentation context: `SPEC.md` as canonical source, distinction between `analyzer` app and `redline_bob` project package, stubs vs implementation

**[`.bob/rules-plan/AGENTS.md`](.bob/rules-plan/AGENTS.md)** — Architectural constraints: sequential pipeline must be preserved, ordinal severity scoring rule, empty templates directory, settings split convention, no test tooling beyond Django's runner