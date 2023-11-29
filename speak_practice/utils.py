import logging
import sys


def get_logger(name):
    logging.basicConfig(format=(
        f"%(asctime)s - %(name)s - "
        f"%(levelname)s - %(message)s"),
        level=logging.INFO)
    return logging.getLogger(name)


StdOutHandler = logging.StreamHandler(sys.stdout)
StdOutHandler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s | %(levelname)s >>> %(message)s')
StdOutHandler.setFormatter(formatter)
StdOutHandler.setStream(stream=sys.stdout)
