import time
from typing import Any

import polars as pl
import pymysql
import pymysql.cursors

from app.connectors.base import (
    BaseConnector, SchemaColumn, ConnectionTestResult, WriteResult,
    ConnectionException, SchemaException, DataException,
)

MYSQL_TYPE_MAP = {
    "int": "INTEGER", "bigint": "BIGINT", "smallint": "SMALLINT", "tinyint": "SMALLINT",
    "float": "FLOAT", "double": "DOUBLE", "decimal": "DECIMAL", "numeric": "DECIMAL",
    "varchar": "VARCHAR", "text": "TEXT", "mediumtext": "TEXT", "longtext": "TEXT",
    "char": "CHAR", "enum": "VARCHAR",
    "boolean": "BOOLEAN", "bool": "BOOLEAN",
    "date": "DATE", "datetime": "TIMESTAMP", "timestamp": "TIMESTAMP", "time": "TIME",
    "json": "JSON",
}


class MySQLConnector(BaseConnector):

    def _connect(self):
        try:
            return pymysql.connect(
                host=self.config.get("host"),
                port=self.config.get("port", 3306),
                database=self.config.get("database_name"),
                user=self.config.get("username"),
                password=self.config.get("password"),
                charset=self.config.get("extra_config", {}).get("charset", "utf8mb4"),
                connect_timeout=10,
                cursorclass=pymysql.cursors.DictCursor,
            )
        except pymysql.OperationalError as e:
            raise ConnectionException("CONNECTION_FAILED", f"MySQL bağlantısı kurulamadı: {self.config.get('host')}", str(e))

    def test_connection(self) -> ConnectionTestResult:
        start = time.monotonic()
        try:
            conn = self._connect()
            with conn.cursor() as cur:
                cur.execute("SELECT VERSION()")
                version = cur.fetchone()["VERSION()"]
            conn.close()
            return ConnectionTestResult(success=True, latency_ms=int((time.monotonic() - start) * 1000), server_version=version)
        except ConnectionException as e:
            return ConnectionTestResult(success=False, error=e.message)
        except Exception as e:
            return ConnectionTestResult(success=False, error=str(e))

    def list_tables(self) -> list[str]:
        db = self.config.get("database_name")
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_type = 'BASE TABLE' ORDER BY table_name", (db,))
                return [row["table_name"] for row in cur.fetchall()]
        finally:
            conn.close()

    def get_schema(self, table_name: str) -> list[SchemaColumn]:
        db = self.config.get("database_name")
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT column_name, data_type, is_nullable, numeric_precision, numeric_scale, character_maximum_length "
                    "FROM information_schema.columns WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
                    (db, table_name)
                )
                rows = cur.fetchall()
                if not rows:
                    raise SchemaException("TABLE_NOT_FOUND", f"Tablo bulunamadı: {table_name}")
                return [
                    SchemaColumn(
                        name=r["column_name"],
                        data_type=MYSQL_TYPE_MAP.get(r["data_type"].lower(), r["data_type"].upper()),
                        is_nullable=r["is_nullable"] == "YES",
                        precision=r["numeric_precision"],
                        scale=r["numeric_scale"],
                        max_length=r["character_maximum_length"],
                    )
                    for r in rows
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
            sql, params = query, []
        else:
            sql = f"SELECT * FROM `{table}`"
            params = []
            if checkpoint_col and checkpoint_value:
                sql += f" WHERE `{checkpoint_col}` > %s"
                params.append(checkpoint_value)
            if limit:
                sql += f" LIMIT {int(limit)}"

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params or None)
                rows = cur.fetchall()
                return pl.from_dicts(rows) if rows else pl.DataFrame()
        except Exception as e:
            raise DataException("READ_FAILED", f"Veri okunamadı: {table}", str(e))
        finally:
            conn.close()

    def write_data(self, df: pl.DataFrame, write_config: dict[str, Any]) -> WriteResult:
        table = write_config["table"]
        mode = write_config.get("mode", "APPEND").upper()

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                if mode in ("FULL_LOAD", "TRUNCATE_INSERT"):
                    cur.execute(f"TRUNCATE TABLE `{table}`")
                cols = df.columns
                col_names = ", ".join([f"`{c}`" for c in cols])
                placeholders = ", ".join(["%s"] * len(cols))
                sql = f"INSERT INTO `{table}` ({col_names}) VALUES ({placeholders})"
                rows = [tuple(r) for r in df.iter_rows()]
                cur.executemany(sql, rows)
            conn.commit()
            return WriteResult(rows_written=len(rows))
        except Exception as e:
            conn.rollback()
            raise DataException("WRITE_FAILED", f"MySQL yazma başarısız: {table}", str(e))
        finally:
            conn.close()
