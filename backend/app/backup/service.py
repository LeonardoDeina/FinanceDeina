import datetime as dt
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

_SAFE_FILENAME = re.compile(r"^financedeina_\d{8}_\d{6}\.sql$")

from app.core.config import get_settings

APP_SCHEMA_VERSION = "1.0"
BACKUP_HEADER_PREFIX = f"-- financedeina-backup-schema-version:{APP_SCHEMA_VERSION}"


class BackupError(Exception):
    pass


def _mysql_connection_args() -> list[str]:
    parsed = urlparse(get_settings().database_url.replace("mysql+pymysql", "mysql"))
    args = ["-h", parsed.hostname or "localhost", "-P", str(parsed.port or 3306), "-u", parsed.username or "root"]
    if parsed.password:
        args.append(f"-p{parsed.password}")
    return args, (parsed.path or "/").lstrip("/")


def _backup_dir() -> Path:
    path = Path(get_settings().backup_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def create_backup() -> Path:
    """BKP-001: local dump named with date/time; confirms completion by existing on disk."""
    connection_args, database = _mysql_connection_args()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    target = _backup_dir() / f"financedeina_{timestamp}.sql"

    try:
        result = subprocess.run(
            ["mysqldump", *connection_args, "--single-transaction", "--routines", database],
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise BackupError(f"mysqldump indisponível: {exc}") from exc
    if result.returncode != 0:
        raise BackupError(result.stderr)

    target.write_text(f"{BACKUP_HEADER_PREFIX}\n{result.stdout}")
    return target


def list_backups() -> list[Path]:
    return sorted(_backup_dir().glob("financedeina_*.sql"), reverse=True)


def restore_backup(filename: str) -> None:
    """BKP-002: validates the schema-version header before touching the live database."""
    if not _SAFE_FILENAME.match(filename):
        raise BackupError("Nome de arquivo de backup inválido.")
    target = _backup_dir() / filename
    if not target.exists():
        raise BackupError("Arquivo de backup não encontrado.")

    with target.open() as handle:
        first_line = handle.readline().strip()
    if not first_line.startswith("-- financedeina-backup-schema-version:"):
        raise BackupError("Arquivo de backup inválido ou de versão incompatível.")

    connection_args, database = _mysql_connection_args()
    try:
        with target.open() as handle:
            handle.readline()  # skip header
            result = subprocess.run(
                ["mysql", *connection_args, database], stdin=handle, capture_output=True, text=True
            )
    except OSError as exc:
        raise BackupError(f"cliente mysql indisponível: {exc}") from exc
    if result.returncode != 0:
        raise BackupError(result.stderr)
