"""Storage adapters, loaded lazily for runtimes without SQLite support."""

__all__ = ["SQLiteStore"]


def __getattr__(name: str):
    if name == "SQLiteStore":
        from wallet_vitals.storage.sqlite import SQLiteStore

        return SQLiteStore
    raise AttributeError(name)
