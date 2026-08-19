# Mac Machine Setup

## Objective

Prepare a clean, reproducible Novi development machine.

## Required

- macOS with current supported updates;
- Git;
- Xcode Command Line Tools;
- Homebrew;
- Python 3.x matching the repository's pinned version;
- Node.js only if repository tooling requires it;
- Docker Desktop only for services that require containers;
- GitHub CLI optional for local workflow inspection.

## Rules

Do not install project dependencies globally when a repository environment can provide them. Prefer project-local virtual environments and pinned dependency files.

## Verification

Record versions of Git, Python, Node, Docker and relevant build tools in the local test report.

## Security

Never commit tokens, credentials, private keys or local `.env` files. Use GitHub secrets or local ignored configuration where required.
