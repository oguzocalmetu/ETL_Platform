import time
from typing import Any, Optional

import polars as pl
import psycopg2
import psycopg2.extras

from app.connectors.base import (
    BaseConnector, SchemaColumn, ConnectionTestResult, WriteResult,
    ConnectionException, SchemaException, DataException,
)

PG_TYPE_MAP = {
    "integer": "INTEGER", "int4": "INTEGER", "int8": "BIGINT", "bigint": "BIGINT",
    "smallint": "SMALLINT", "int2": "SMALLINT",
    "numeric": "DECIMAL", "decimal": "DECIMAL", "float4": "FLOAT", "float8": "DOUBLE",
    "real": "FLOAT", "double precision": "DOUBLE",
    "varchar": "VARCHAR", "character varying": "VARCHAR", "text": "TEXT",
    "char": "CHAR", "bpchar": "CHAR",
    "boolean": "BOOLEAN", "bool": "BOOLEAN",
    "date": "DATE", "timestamp": "TIMESTAMP", "timestamptz": "TIMESTAMPTZ",
    "time": "TIME", "json": "JSON", "jsonb": "JSONB", "uuid": "UUID",
}


class PostgreSQLConnector(BaseConnector):

    def _connect(self) -> psycopg2.extensions.connection:
        try:
            conn = psycopg2.connect(
                host=self.config.get("host"),
                port=self.config.get("port", 5432),
                dbname=self.config.get("database_name"),
                user=self.config.get("username"),
                password=self.config.get("password"),
                connect_timeout=10,
                sslmode=self.config.get("extra_config", {}).get("sslmode", "prefer"),
            )
            return conn
        except psycopg2.OperationalError as e:
            raise ConnectionException(
                "CONNECTION_FAILED",
                f"PostgreSQL bağlantısı kurulamadı: {self.config.get('host')}",
                str(e),
            )

    def test_connection(self) -> ConnectionTestResult:
        start = time.monotonic()
        try:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
            conn.close()
            latency = int((time.monotonic() - start) * 1000)
            return ConnectionTestResult(success=True, latency_ms=latency, server_version=version[:50])
        except ConnectionException as e:
            return ConnectionTestResult(success=False, error=e.message)
        except Exception as e:
            return ConnectionTestResult(success=False, error=str(e))

    def list_tables(self) -> list[str]:
        schema = self.config.get("extra_config", {}).get("schema", "public")
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = %s AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    """,
                    (schema,),
                )
                return [row[0] for row in cur.fetchall()]
        finally:
            conn.close()

    def get_schema(self, table_name: str) -> list[SchemaColumn]:
        schema = self.config.get("extra_config", {}).get("schema", "public")
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        numeric_precision,
                        numeric_scale,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s
                    ORDER BY ordinal_position
                    """,
                    (schema, table_name),
                )
                rows = cur.fetchall()
                if not rows:
                    raise SchemaException("TABLE_NOT_FOUND", f"Tablo bulunamadı: {table_name}")
                return [
                    SchemaColumn(
                        name=row[0],
                        data_type=PG_TYPE_MAP.get(row[1].lower(), row[1].upper()),
                        is_nullable=row[2] == "YES",
                        precision=row[3],
                        scale=row[4],
                        max_length=row[5],
                    )
                    for row in rows
                ]
        finally:
            conn.close()

    def read_data(self, read_config: dict[str, Any]) -> pl.DataFrame:
        table = read_config.get("table")
        query = read_config.get("query")
        checkpoint_col = read_config.get("checkpoint_col")
        checkpoint_value = read_config.get("checkpoint_value")
        limit = read_config.get("limit")

        if query:
            sql = query
            params = []
        else:
            schema = self.config.get("extra_config", {}).get("schema", "public")
            sql = f'SELECT * FROM "{schema}"."{table}"'
            params = []
            if checkpoint_col and checkpoint_value:
                sql += f" WHERE {checkpoint_col} > %s"
                params.append(checkpoint_value)
            if limit:
                sql += f" LIMIT {int(limit)}"

        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params or None)
                rows = cur.fetchall()
                if not rows:
                    return pl.DataFrame()
                return pl.from_dicts([dict(r) for r in rows])
        except Exception as e:
            raise DataException("READ_FAILED", f"Veri okunamadı: {table or 'custom query'}", str(e))
        finally:
            conn.close()

    def write_data(self, df: pl.DataFrame, write_config: dict[str, Any]) -> WriteResult:
        table = write_config["table"]
        mode = write_config.get("mode", "APPEND").upper()
        upsert_keys = write_config.get("upsert_keys", [])
        schema = self.config.get("extra_config", {}).get("schema", "public")

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                if mode in ("FULL_LOAD", "TRUNCATE_INSERT"):
                    cur.execute(f'TRUNCATE TABLE "{schema}"."{table}"')

                cols = df.columns
                placeholders = ", ".join(["%s"] * len(cols))
                col_names = ", ".join([f'"{c}"' for c in cols])

                if mode == "UPSERT" and upsert_keys:
                    conflict_cols = ", ".join([f'"{k}"' for k in upsert_keys])
                    update_set = ", ".join([f'"{c}" = EXCLUDED."{c}"' for c in cols if c not in upsert_keys])
                    sql = (
                        f'INSERT INTO "{schema}"."{table}" ({col_names}) VALUES ({placeholders}) '
                        f'ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_set}'
                    )
                else:
                    sql = f'INSERT INTO "{schema}"."{table}" ({col_names}) VALUES ({placeholders})'

                rows = [tuple(row) for row in df.iter_rows()]
                psycopg2.extras.execute_batch(cur, sql, rows, page_size=1000)
                conn.commit()
                return WriteResult(rows_written=len(rows))
        except Exception as e:
            conn.rollback()
            raise DataException("WRITE_FAILED", f"Hedefe yazma başarısız: {table}", str(e))
        finally:
            conn.close()
