import time
from pathlib import Path
from typing import Any

import polars as pl

from app.connectors.base import (
    BaseConnector, SchemaColumn, ConnectionTestResult, WriteResult,
    ConnectionException, DataException,
)

POLARS_TO_SCHEMA_TYPE = {
    pl.Int32: "INTEGER", pl.Int64: "BIGINT", pl.Float32: "FLOAT",
    pl.Float64: "DOUBLE", pl.Utf8: "VARCHAR", pl.String: "VARCHAR",
    pl.Boolean: "BOOLEAN", pl.Date: "DATE", pl.Datetime: "TIMESTAMP",
}


class CSVConnector(BaseConnector):
    """Connector for local CSV files. config.extra_config may contain delimiter, encoding."""

    def _get_path(self) -> Path:
        path_str = self.config.get("extra_config", {}).get("file_path") or self.config.get("host", "")
        p = Path(path_str)
        return p

    def test_connection(self) -> ConnectionTestResult:
        start = time.monotonic()
        try:
            p = self._get_path()
            if not p.exists():
                return ConnectionTestResult(success=False, error=f"Dosya bulunamadı: {p}")
            if p.suffix.lower() not in (".csv", ".tsv", ".txt"):
                return ConnectionTestResult(success=False, error="Dosya CSV formatında değil")
            latency = int((time.monotonic() - start) * 1000)
            return ConnectionTestResult(success=True, latency_ms=latency, server_version=f"CSV ({p.stat().st_size // 1024}KB)")
        except Exception as e:
            return ConnectionTestResult(success=False, error=str(e))

    def list_tables(self) -> list[str]:
        """For CSV, tables = the file itself."""
        p = self._get_path()
        return [p.name]

    def get_schema(self, table_name: str) -> list[SchemaColumn]:
        p = self._get_path()
        delimiter = self.config.get("extra_config", {}).get("delimiter", ",")
        try:
            df = pl.read_csv(p, separator=delimiter, n_rows=0, infer_schema_length=1000)
            return [
                SchemaColumn(
                    name=col,
                    data_type=POLARS_TO_SCHEMA_TYPE.get(type(df.schema[col]), "VARCHAR"),
                    is_nullable=True,
                )
                for col in df.columns
            ]
        except Exception as e:
            raise DataException("SCHEMA_FAILED", f"CSV şeması okunamadı: {p}", str(e))

    def read_data(self, read_config: dict[str, Any]) -> pl.DataFrame:
        p = self._get_path()
        delimiter = self.config.get("extra_config", {}).get("delimiter", ",")
        encoding = self.config.get("extra_config", {}).get("encoding", "utf8")
        limit = read_config.get("limit")
        try:
            df = pl.read_csv(
                p,
                separator=delimiter,
                encoding=encoding,
                n_rows=limit,
                infer_schema_length=10000,
                null_values=["", "NULL", "null", "NA", "N/A"],
            )
            return df
        except Exception as e:
            raise DataException("READ_FAILED", f"CSV dosyası okunamadı: {p}", str(e))

    def write_data(self, df: pl.DataFrame, write_config: dict[str, Any]) -> WriteResult:
        output_path = write_config.get("output_path") or str(self._get_path().parent / "output.csv")
        delimiter = self.config.get("extra_config", {}).get("delimiter", ",")
        try:
            df.write_csv(output_path, separator=delimiter)
            return WriteResult(rows_written=len(df))
        except Exception as e:
            raise DataException("WRITE_FAILED", f"CSV yazma başarısız: {output_path}", str(e))
