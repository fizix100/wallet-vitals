from pathlib import Path

from fastapi.testclient import TestClient

from wallet_vitals.config import Settings
from wallet_vitals.web.app import create_app


def test_home_and_health_work_without_api_key(tmp_path: Path) -> None:
    app = create_app(
        Settings(
            graph_api_key=None,
            database_path=tmp_path / "web.db",
        )
    )
    with TestClient(app) as client:
        home = client.get("/")
        report_page = client.get("/reports/missing-report")
        health = client.get("/health")
        analysis = client.post(
            "/api/analyze",
            json={"address": "0x1111111111111111111111111111111111111111"},
        )

    assert home.status_code == 200
    assert "Wallet Vitals" in home.text
    assert report_page.status_code == 200
    assert health.json()["graph_configured"] is False
    assert analysis.status_code == 503
