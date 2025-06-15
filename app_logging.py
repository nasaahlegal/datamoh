import logging

logging.basicConfig(
    filename='log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def log_event(event: str):
    logging.info(event)

def log_error(error: str):
    logging.error(error)