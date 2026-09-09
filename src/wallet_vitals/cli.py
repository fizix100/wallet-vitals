import uvicorn


def main() -> None:
    uvicorn.run(
        "wallet_vitals.web.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
