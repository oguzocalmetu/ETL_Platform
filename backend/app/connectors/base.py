from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any
import polars as pl


@dataclass
class SchemaColumn:
    name: str
    data_type: str
    is_nullable: bool = True
    precision: Optional[int] = None
    scale: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class ConnectionTestResult:
    success: bool
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    server_version: Optional[str] = None


@dataclass
class WriteResult:
    rows_written: int
    rows_skipped: int = 0


class DataFlowException(Exception):
    def __init__(self, code: str, message: str, detail: str = None):
        super().__init__(message)
        self.code = code
        self.message = message      # User-friendly
        self.detail = detail        # Technical (for logs)


class ConnectionException(DataFlowException):
    pass


class SchemaException(DataFlowException):
    pass


class DataException(DataFlowException):
    pass


class BaseConnector(ABC):
    """Abstract base class for all DataFlow source/target connectors."""

    def __init__(self, config: dict[str, Any]):
        self.config = config

    @abstractmethod
    def test_connection(self) -> ConnectionTestResult:
        """Test connectivity. Returns result — does NOT raise."""

    @abstractmethod
    def get_schema(self, table_name: str) -> list[SchemaColumn]:
        """Return column definitions for a given table/sheet/file."""

    @abstractmethod
    def list_tables(self) -> list[str]:
        """Return available tables, files, or sheets."""

    @abstractmethod
    def read_data(self, read_config: dict[str, Any]) -> pl.DataFrame:
        """
        Read data from source.

        read_config keys:
          - table: str (or None if query is set)
          - query: str (custom SQL / None)
          - checkpoint_col: str | None
          - checkpoint_value: str | None
          - limit: int | None (for test runs)
          - batch_size: int
        """

    def write_data(self, df: pl.DataFrame, write_config: dict[str, Any]) -> WriteResult:
        """
        Write DataFrame to target.

        write_config keys:
          - table: str
          - mode: APPEND | FULL_LOAD | TRUNCATE_INSERT | UPSERT | INCREMENTAL
          - upsert_keys: list[str]
          - create_if_not_exists: bool

        Override in target connectors.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support write operations.")

    def preview_data(self, table: str, limit: int = 20) -> pl.DataFrame:
        """Return a sample of rows for UI preview. Default uses read_data."""
        return self.read_data({"table": table, "limit": limit, "batch_size": limit})

    def validate_query(self, query: str) -> bool:
        """Check if a custom SQL query is syntactically valid. Override if supported."""
        return True

    def close(self):
        """Release any open connections or file handles."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
