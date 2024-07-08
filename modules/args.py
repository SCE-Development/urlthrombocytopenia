import argparse
import time


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--database-file-path",
        required=True,
        help="path to sqlite database file"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="ip address for server to listen on, defaults to 0.0.0.0"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="port for server to be hosted on, defaults to 8000"
    )
    parser.add_argument(
        "--disable-random-alias",
        action= "store_true",
        help="disable generating randomly hashed aliases"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="increase logging verbosity; can be used multiple times",
    )
    parser.add_argument(
        "--cache-size",
        type=int,
        default=100,
        help="number of url redirects to store in memory. defaults to 100"
    )
    parser.add_argument(
        "--qr-code-cache-path",
        required=True,
        help="the folder to store generated url files"
    )
    parser.add_argument(
        "--qr-code-cache-size",
        type=int,
        default=100,
        help="maxmimum number of qr codes to store before removing files"
    )
    parser.add_argument(
        "--qr-code-base-url",
        required=True,
        help="the base url set to http://localhost:8000"
    )
    parser.add_argument(
        "--qr-code-center-image-path",
        default=None,
        help="the base url path for the center image in qr code"
    )
    parser.add_argument(
        "--cache-state-file",
        required=True,
        help="the JSON file where the cache will map to"
    )
    
    return parser.parse_args()
