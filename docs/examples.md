# Examples

The scripts below are in [`examples/`](https://github.com/moseleydev/swarm-kit/tree/main/examples).
Add your API key to `.env`, then run them from the repository root, for example
`python examples/customer_support.py`.

| Example | Shows |
| --- | --- |
| [`customer_support.py`](https://github.com/moseleydev/swarm-kit/blob/main/examples/customer_support.py) | Unsupervised mode: triage that transfers to Billing or Tech, and a plain-function refund tool. |
| [`content_pipeline.py`](https://github.com/moseleydev/swarm-kit/blob/main/examples/content_pipeline.py) | Supervised mode: Researcher, then Copywriter, then Editor. |
| [`unsupervised_chat.py`](https://github.com/moseleydev/swarm-kit/blob/main/examples/unsupervised_chat.py) | Async chat with async tools and async save/load hooks across two turns. |
| [`supervised_pipeline.py`](https://github.com/moseleydev/swarm-kit/blob/main/examples/supervised_pipeline.py) | Async supervised extraction into the global state. |
| [`fastapi_server.py`](https://github.com/moseleydev/swarm-kit/blob/main/examples/fastapi_server.py) | A `/chat` endpoint with one isolated session per user. |

## Customer support (unsupervised)

```python
--8<-- "examples/customer_support.py"
```

## FastAPI server

```python
--8<-- "examples/fastapi_server.py"
```

Have an example to share, such as a different database, framework or provider? Contributions
are welcome. See [Contributing](contributing.md).
