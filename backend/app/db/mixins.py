import datetime as dt

from sqlalchemy import DateTime
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import Mapped, mapped_column

# DATETIME(6) on MySQL (microsecond precision, per spec's data model), plain
# DATETIME elsewhere (e.g. SQLite in tests) since `fsp` is a MySQL-only arg.
UTCDateTime = DateTime().with_variant(mysql.DATETIME(fsp=6), "mysql")


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)


class TimestampMixin:
    created_at: Mapped[dt.datetime] = mapped_column(UTCDateTime, default=utcnow, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow, nullable=False)
