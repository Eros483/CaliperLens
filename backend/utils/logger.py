import logging
import os
import uuid
from datetime import datetime

from pythonjsonlogger import jsonlogger

LOGS_DIR = "logs"
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, f"log_{datetime.now().strftime('%Y-%m-%d')}.log")


class _TraceInjector(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "trace_id"):
            record.trace_id = getattr(record, "trace_id", str(uuid.uuid4())[:8])
        if not hasattr(record, "session_id"):
            record.session_id = getattr(record, "session_id", "-")
        if not hasattr(record, "node"):
            record.node = getattr(record, "node", "-")
        return True


_formatter = jsonlogger.JsonFormatter(
    fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

_file_handler = logging.FileHandler(LOG_FILE)
_file_handler.setFormatter(_formatter)
_file_handler.addFilter(_TraceInjector())

_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_formatter)
_stream_handler.addFilter(_TraceInjector())


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        logger.addHandler(_file_handler)
        logger.addHandler(_stream_handler)
    return logger
