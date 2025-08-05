# Contributing to Windows-MCP

Thank you for your interest in contributing to Windows-MCP! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Getting Started](#getting-started)
  - [Development Environment](#development-environment)
  - [Installation from Source](#installation-from-source)
- [Development Workflow](#development-workflow)
  - [Branching Strategy](#branching-strategy)
  - [Commit Messages](#commit-messages)
  - [Code Style](#code-style)
  - [Pre-commit Hooks](#pre-commit-hooks)
- [Testing](#testing)
  - [Running Tests](#running-tests)
  - [Adding Tests](#adding-tests)
- [Pull Requests](#pull-requests)
  - [Creating a Pull Request](#creating-a-pull-request)
  - [Pull Request Template](#pull-request-template)
- [Documentation](#documentation)
- [Release Process](#release-process)
- [Getting Help](#getting-help)

## Getting Started

### Development Environment

Windows-MCP requires:
- Python 3.13 or later

### Installation from Source

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/windows-MCP.git
   cd windows-mcp
   ```
3. Install the package in development mode:
   ```bash
   pip install -e ".[dev,search]"
   ```
4. Set up pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### Branching Strategy

- `main` branch contains the latest stable code
- Create feature branches from `main` named according to the feature you're implementing: `feature/your-feature-name`
- For bug fixes, MCP: `fix/bug-description`

### Commit Messages

For now no commit style is enforced, try to keep your commit messages informational.
### Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for code formatting and linting. The configuration is in `ruff.toml`.

Key style guidelines:
- Line length: 100 characters
- MCP double quotes for strings
- Follow PEP 8 naming conventions
- Add type hints to function signatures

### Pre-commit Hooks

We use pre-commit hooks to ensure code quality before committing. The configuration is in `.pre-commit-config.yaml`.

The hooks will:
- Format code using Ruff
- Run linting checks
- Check for trailing whitespace and fix it
- Ensure files end with a newline
- Validate YAML files
- Check for large files
- Remove debug statements

## Testing

### Running Tests

Run the test suite with pytest:

```bash
pytest
```

To run specific test categories:

```bash
pytest tests/
```

### Adding Tests

- Add unit tests for new functionality in `tests/unit/`
- For slow or network-dependent tests, mark them with `@pytest.mark.slow` or `@pytest.mark.integration`
- Aim for high test coverage of new code

## Pull Requests

### Creating a Pull Request

1. Ensure your code passes all tests and pre-commit hooks
2. Push your changes to your fork
3. Submit a pull request to the main repository
4. Follow the pull request template

## Documentation

- Update docstrings for new or modified functions, classes, and methods
- MCP Google-style docstrings:
  ```python
  def function_name(param1: type, param2: type) -> return_type:
      """Short description.

      Longer description if needed.

      Args:
          param1: Description of param1
          param2: Description of param2

      Returns:
          Description of return value

      Raises:
          ExceptionType: When and why this exception is raised
      """
  ```
- Update README.md for user-facing changes

## GUI Development Guide (GUI 開發指南)

### Architecture Overview (架構概覽)

The GUI application follows a modular architecture with the following key components:

#### Main Window Structure (主視窗結構)
- **Location**: `src/gui/main_window.py`
- **Features**: Complete menu bar, unified navigation, status bar, responsive layout
- **Entry Point**: `src/gui/scheduler_app.py` - handles configuration and lifecycle management

#### Navigation System (導航系統)
Five main pages following the design specifications:
1. **Overview** - System statistics and recent activity
2. **Schedules** - Task management and scheduling
3. **Apps** - Application monitoring
4. **Logs** - Execution history and logging
5. **Settings** - System configuration

#### Key Components (核心組件)

##### Schedule Dialog (排程對話框)
- **Location**: `src/gui/dialogs/schedule_dialog.py`
- **Features**: Multi-tab interface for task creation/editing
- **Tabs**: Basic Info, Schedule Settings, Action Settings, Options, Preview

##### Action Sequence Widget (動作序列組件)
- **Location**: `src/gui/widgets/action_sequence_widget.py`
- **Features**: Support for multiple actions, drag-and-drop reordering, validation

##### Execution Preview (執行預覽)
- **Location**: `src/gui/widgets/execution_preview_widget.py`
- **Features**: Real-time preview of task execution, timeline estimation

### Development Guidelines (開發指南)

#### Widget Development (組件開發)
1. Follow the existing widget structure in `src/gui/widgets/`
2. Implement proper event handling and callbacks
3. Use consistent styling and layout patterns
4. Add proper validation and error handling

#### Page Development (頁面開發)
1. Extend the base page structure in `src/gui/pages/`
2. Implement the required interface methods
3. Handle navigation and state management
4. Ensure responsive design

#### Model Integration (模型整合)
1. Use the action sequence model for complex automations
2. Implement proper task validation
3. Handle backward compatibility with old task formats
4. Follow the execution options pattern

### Testing GUI Components (GUI 組件測試)

#### Manual Testing
1. Test all user interactions and workflows
2. Verify responsive design across different screen sizes
3. Test keyboard shortcuts and accessibility features
4. Validate error handling and edge cases

#### Integration Testing
1. Test task creation and execution workflows
2. Verify data persistence and loading
3. Test cross-component communication
4. Validate schedule execution and monitoring

## Getting Help

If you need help with your contribution:

- Open an issue for discussion
- Reach out to the maintainers
- Check existing code for examples
- Refer to the GUI development guide above for component-specific guidance

Thank you for contributing to Windows-MCP!