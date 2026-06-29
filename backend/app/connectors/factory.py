from app.connectors.base import BaseConnector
from app.connectors.postgres import PostgreSQLConnector
from app.connectors.csv_connector import CSVConnector

# Import others as they are implemented
try:
    from app.connectors.mysql import MySQLConnector
    _MYSQL_AVAILABLE = True
except ImportError:
    _MYSQL_AVAILABLE = False

try:
    from app.connectors.mssql import MSSQLConnector
    _MSSQL_AVAILABLE = True
except ImportError:
    _MSSQL_AVAILABLE = False

try:
    from app.connectors.excel_connector import ExcelConnector
    _EXCEL_AVAILABLE = True
except ImportError:
    _EXCEL_AVAILABLE = False


CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "POSTGRESQL": PostgreSQLConnector,
    "CSV": CSVConnector,
}

if _MYSQL_AVAILABLE:
    CONNECTOR_REGISTRY["MYSQL"] = MySQLConnector
if _MSSQL_AVAILABLE:
    CONNECTOR_REGISTRY["MSSQL"] = MSSQLConnector
if _EXCEL_AVAILABLE:
    CONNECTOR_REGISTRY["EXCEL"] = ExcelConnector


def create_connector(conn_type: str, config: dict) -> BaseConnector:
    """
    Factory function — creates and returns the appropriate connector instance.
    config should include decrypted credentials.
    """
    key = conn_type.upper()
    cls = CONNECTOR_REGISTRY.get(key)
    if cls is None:
        available = list(CONNECTOR_REGISTRY.keys())
        raise ValueError(f"Desteklenmeyen connector tipi: '{conn_type}'. Mevcut: {available}")
    return cls(config)


def list_supported_types() -> list[str]:
    return list(CONNECTOR_REGISTRY.keys())
