import logging
import json

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
