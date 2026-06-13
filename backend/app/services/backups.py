import shutil
from datetime import datetime
from pathlib import Path

from app.config import DATA_DIR, settings


BACKUP_DIR = DATA_DIR / "backups"


def _sqlite_path() -> Path | None:
    prefix = "sqlite:///"
    if not settings.database_url.startswith(prefix):
        return None
    return Path(settings.database_url.removeprefix(prefix))


def create_backup() -> dict:
    db_path = _sqlite_path()
    if db_path is None or not db_path.exists():
        raise FileNotFoundError("SQLite 数据库文件不存在")
    BACKUP_DIR.mkdir(exist_ok=True)
    filename = f"3dcost-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
    target = BACKUP_DIR / filename
    shutil.copy2(db_path, target)
    return backup_info(target)


def backup_info(path: Path) -> dict:
    stat = path.stat()
    return {
        "filename": path.name,
        "size_bytes": stat.st_size,
        "created_at": datetime.fromtimestamp(stat.st_mtime),
    }


def list_backups() -> list[dict]:
    BACKUP_DIR.mkdir(exist_ok=True)
    return [
        backup_info(path)
        for path in sorted(BACKUP_DIR.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    ]
