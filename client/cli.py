import argparse
from ipaddress import IPv4Address
import logging
import os

from .client import TuiClashApp


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        type=IPv4Address,
        help="ip address of the host",
        default=IPv4Address("127.0.0.1"),
    )
    parser.add_argument("-p", "--port", type=int, help="port to use", default=1335)
    args = parser.parse_args()
    if os.getenv("DEBUG") is None:
        logging.basicConfig(filename="tui-clash.log", level=logging.INFO)
    else:
        logging.basicConfig(filename="tui-clash.log", level=logging.DEBUG)
    logging.info("TuiClashApp is starting...")
    TuiClashApp(str(args.host), args.port).run()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
