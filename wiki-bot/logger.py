import logging
import json
import sys

logger = logging.getLogger("LangGraphLogger")
logger.setLevel(logging.INFO)

# Console handler with custom formatter
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter(
    '{"level": "%(levelname)s", "node": "%(node)s", "message": %(message)s}'
)
ch.setFormatter(formatter)
logger.addHandler(ch)


# Helper to log structured messages
def log_node(node_name: str, message: dict, level=logging.INFO):
    logger.log(level, json.dumps(message), extra={"node": node_name})


last_len = 0


def update_line(text):
    """Replaces previous line with the given text"""
    global last_len
    sys.stdout.write("\r" + text + " " * max(0, last_len - len(text)))
    sys.stdout.flush()
    last_len = len(text)
