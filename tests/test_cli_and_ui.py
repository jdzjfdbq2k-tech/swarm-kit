import json

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from swarm_kit.cli.main import app
from swarm_kit.ui import server

runner = CliRunner()


def test_init_creates_project_and_refuses_to_overwrite(tmp_path):
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0, result.output
    main_file = tmp_path / "agents" / "main.py"
    assert "from swarm_kit import Agent, Swarm" in main_file.read_text()
    assert (tmp_path / ".env.example").exists()

    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 1
    assert runner.invoke(app, ["init", str(tmp_path), "--force"]).exit_code == 0


def test_generated_template_is_valid_python(tmp_path):
    runner.invoke(app, ["init", str(tmp_path)])
    compile((tmp_path / "agents" / "main.py").read_text(), "main.py", "exec")


def test_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "swarm-agent-kit" in result.output


def test_logs_endpoint_skips_partial_lines(tmp_path, monkeypatch):
    log = tmp_path / "runs.jsonl"
    log.write_text(json.dumps({"agent": "A", "action": "Start", "content": "hi"}) + "\n{\"partial\": ")
    monkeypatch.setenv("SWARM_KIT_LOG_FILE", str(log))
    client = TestClient(server.app)
    assert client.get("/api/logs").json() == {"logs": [{"agent": "A", "action": "Start", "content": "hi"}]}
    assert "Agent Studio" in client.get("/").text
