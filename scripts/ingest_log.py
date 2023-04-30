from log_parsing.parse_access_log import parse_ingest_file
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    args = parser.parse_args()
    with open(args.file) as f:
        parse_ingest_file(f)
