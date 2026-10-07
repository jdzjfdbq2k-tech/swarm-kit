# Security Policy

## Supported versions

Security fixes are released for the latest minor version on PyPI.

| Version | Supported |
| ------- | --------- |
| 0.2.x   | ✅        |
| < 0.2   | ❌        |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Use GitHub's [private vulnerability reporting](https://github.com/moseleydev/swarm-kit/security/advisories/new)
or email **moseleydev7@gmail.com** with:

- a description of the issue and its impact,
- steps to reproduce (a minimal script is ideal),
- the affected version(s).

You should receive an acknowledgement within 72 hours. Once a fix is ready we will
publish a release and credit you in the changelog unless you prefer otherwise.

## Things to keep in mind when using Swarm Kit

- **Tools run with your application's permissions.** An LLM decides when to call them
  and with which arguments, so validate arguments inside every tool as you would any
  untrusted input, and never expose destructive tools without a confirmation step.
- **The Agent Studio is a local development tool.** It binds to `127.0.0.1` by default and
  has no authentication. Don't expose it publicly; the log it serves contains full prompts
  and tool results.
- **Keep API keys out of source control.** Use a `.env` file (already in `.gitignore`) or
  your platform's secret manager.
