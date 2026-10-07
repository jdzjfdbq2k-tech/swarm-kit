# Contributing to Swarm Agent Kit

First off — thank you! 🐝 Swarm Kit is a small, community-driven project and every
issue, doc fix and pull request makes it better.

## Ways to contribute

- **Report bugs** using the [bug report template](https://github.com/moseleydev/swarm-kit/issues/new?template=bug_report.yml).
- **Suggest features** with the [feature request template](https://github.com/moseleydev/swarm-kit/issues/new?template=feature_request.yml).
- **Pick up an issue** labelled [`good first issue`](https://github.com/moseleydev/swarm-kit/labels/good%20first%20issue)
  or [`help wanted`](https://github.com/moseleydev/swarm-kit/labels/help%20wanted).
  Comment on it first so nobody duplicates your work.
- **Improve the docs** in [`docs/`](https://github.com/moseleydev/swarm-kit/tree/main/docs) — typos and clearer examples are always welcome.
- **Share an example** in [`examples/`](https://github.com/moseleydev/swarm-kit/tree/main/examples) showing Swarm Kit with a real database, framework or provider.

## Development setup

We use [uv](https://docs.astral.sh/uv/) for environments and dependency locking.

```bash
git clone https://github.com/<your-username>/swarm-kit.git
cd swarm-kit
uv sync --group dev          # creates .venv with the package installed in editable mode
uv run pytest                # run the test suite
uv run ruff check src tests examples   # lint
```

Prefer pip? `python -m venv .venv && pip install -e . pytest pytest-asyncio httpx ruff` works too.

The test suite uses a scripted fake LLM (see [`tests/conftest.py`](https://github.com/moseleydev/swarm-kit/blob/main/tests/conftest.py)), so
**no API keys or network access are needed** to run it. Please keep it that way: new
tests should queue fake responses with `llm.queue(make_response(...))` rather than
calling a real provider.

To try the examples against a real model, copy your key into a `.env` file
(`OPENAI_API_KEY=...`, or any [LiteLLM-supported provider](https://docs.litellm.ai/docs/providers)).

## Project layout

```
src/swarm_kit/
├── core/
│   ├── agent.py   # Agent: prompt + model + tools, one LLM call per run()
│   ├── swarm.py   # Swarm: the orchestration engine (both modes, sync + async)
│   ├── tools.py   # function_to_schema(): Python function -> JSON tool schema
│   └── types.py   # AgentOutput, ToolCall, SwarmResult
├── cli/main.py    # `swarm-kit` CLI (init, studio, version)
└── ui/server.py   # Agent Studio dashboard (FastAPI + a single HTML page)
```

`Swarm` implements each mode once, as a generator that *yields* requests (call the LLM,
run a tool, call a DB hook). `_drive_sync` and `_drive_async` fulfil those requests, so a
behaviour change only has to be made in one place and automatically applies to both
`execute()` and `execute_async()`.

## Pull request checklist

1. Fork the repo and create a branch from `main` (`git checkout -b fix/transfer-loop`).
2. Make your change, with a test that fails without it.
3. Run `uv run pytest` and `uv run ruff check src tests examples`.
4. Update the docs in `docs/` if you changed behaviour or public API.
5. Add a line under **Unreleased** in [`CHANGELOG.md`](https://github.com/moseleydev/swarm-kit/blob/main/CHANGELOG.md).
6. Open a PR and fill in the template. Small, focused PRs get reviewed fastest.

We use [Conventional Commits](https://www.conventionalcommits.org/) style messages
(`feat:`, `fix:`, `docs:`, `test:`, `chore:`), but don't worry if you get it wrong — we
can fix it when merging.

## Documentation

Docs are written in Markdown and built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/).

```bash
uv sync --group docs
uv run mkdocs serve          # live preview at http://127.0.0.1:8000
uv run mkdocs build --strict # what CI runs
```

Docs are deployed automatically to GitHub Pages when changes land on `main`.

## Releasing (maintainers)

1. Bump `version` in `pyproject.toml` and move the **Unreleased** changelog entries under the new version.
2. Merge to `main`, then publish a GitHub Release tagged `vX.Y.Z`.
3. The `Publish to PyPI` workflow builds and uploads the package via trusted publishing.

## Code of Conduct

This project follows our [Code of Conduct](https://github.com/moseleydev/swarm-kit/blob/main/CODE_OF_CONDUCT.md). By participating you
agree to uphold it.
