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
    parser.add_argument(
        "-p", "--port", type=int, help="port to connect to", default=1335
    )
    parser.add_argument(
        "-u",
        "--username",
        type=str,
        help="username for submissions",
        default="anonymous",
    )

    args = parser.parse_args()
    if os.getenv("DEBUG") is None:
        logging.basicConfig(filename="tui-clash.log", level=logging.INFO)
    else:
        logging.basicConfig(filename="tui-clash.log", level=logging.DEBUG)

    logging.info("TuiClashApp is starting...")
    app = TuiClashApp(host=str(args.host), port=args.port, username=args.username)
    app.run()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
