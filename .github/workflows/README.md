# GitHub Actions Workflows

This directory contains GitHub Actions workflows for continuous integration and testing.

## Workflows

### Tests (`test.yml`)

Runs on every push and pull request to `main` and `develop` branches.

- **Python versions**: 3.11, 3.12
- **OS**: Ubuntu latest
- **Steps**:
  1. Install uv package manager
  2. Set up Python environment
  3. Install dependencies
  4. Run linting checks (`make lint`)
  5. Run type checking (`make type-check`)
  6. Run tests with coverage reporting (with `SDL_AUDIODRIVER=dummy` to avoid ALSA errors)
  7. Upload coverage reports to Codecov

### Build and Test (`build.yml`)

Runs on every push and pull request to `main` and `develop` branches, plus manual triggers.

- **Python versions**: 3.11, 3.12
- **OS**: Ubuntu, Windows, macOS (latest versions)
- **Steps**:
  1. Install uv package manager
  2. Set up Python environment
  3. Install dependencies
  4. Run tests (with `SDL_AUDIODRIVER=dummy` to avoid ALSA errors)
  5. Verify the game can start (with dummy SDL drivers for headless environment)

## Codecov Integration

To enable Codecov coverage reporting:

1. Sign up at [codecov.io](https://codecov.io) with your GitHub account
2. Add this repository to Codecov
3. Copy the upload token
4. Add the token as a GitHub secret:
   - Go to Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `CODECOV_TOKEN`
   - Value: Your Codecov upload token

## Running Workflows Locally

You can test the workflows locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or see https://github.com/nektos/act for other platforms

# Run the test workflow
act -W .github/workflows/test.yml

# Run the build workflow
act -W .github/workflows/build.yml
```

## Environment Variables

The workflows set the following environment variables to handle headless CI environments:

- `SDL_AUDIODRIVER=dummy` - Prevents ALSA audio errors in GitHub Actions
- `SDL_VIDEODRIVER=dummy` - Prevents video driver errors when testing game startup

## Workflow Status Badges

Add these badges to your main README.md:

```markdown
[![Tests](https://github.com/ansromanov/neon-invanders/actions/workflows/test.yml/badge.svg)](https://github.com/ansromanov/neon-invanders/actions/workflows/test.yml)
[![Build](https://github.com/ansromanov/neon-invanders/actions/workflows/build.yml/badge.svg)](https://github.com/ansromanov/neon-invanders/actions/workflows/build.yml)
[![codecov](https://codecov.io/gh/ansromanov/neon-invanders/branch/main/graph/badge.svg)](https://codecov.io/gh/ansromanov/neon-invanders)
