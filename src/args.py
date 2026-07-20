from argparse import ArgumentParser

from src.table.table import Table


class Args:
    def __init__(self):
        self.arg_parser = ArgumentParser(
            description="Generate a table witgh a specified number of records and the aggregated analytics for de-anonymization."
        )

        self.arg_parser.add_argument(
            "--number-of-records",
            type=int,
            required=True,
            help="Number of records in the table.",
        )
        self.arg_parser.add_argument(
            "--population-value",
            type=float,
            default=0.5,
            help="Population value for the table generation.",
        )
        self.arg_parser.add_argument(
            "--communality-value",
            type=float,
            default=0.25,
            help="Communality value for the table generation.",
        )
        self.arg_parser.add_argument(
            "--titles",
            type=str,
            nargs="*",
            default=[],
            help="List of the initial columns titles",
        )
        self.arg_parser.add_argument(
            "--new-titles",
            type=str,
            nargs="*",
            default=[],
            help="List of the new titles to add.",
        )
        self.arg_parser.add_argument(
            "--sensitive-column",
            type=str,
            default=Table.SENSITIVE_COL_NAME,
            help="Name of the sensitive column in the table.",
        )
        self.arg_parser.add_argument(
            "--level",
            type=str,
            default="INFO",
            help="Set the logging level (DEBUG, INFO, CREATION)",
        )
        self.arg_parser.add_argument(
            "--log-file",
            type=str,
            default=None,
            help="Path to the log file where logs will be saved.",
        )
        self.arg_parser.add_argument(
            "--seed",
            type=int,
            help="Seed for random number generation.",
        )
        self.arg_parser.add_argument(
            "--columns-to-compress",
            type=str,
            nargs="*",
            action="append",
            default=[],
            help="List of columns to compress.",
        )
        self.arg_parser.add_argument(
            "--start-date",
            type=str,
            default=None,
            help="Start date for date-based compression (format: YYYY-MM-DD).",
        )
        self.arg_parser.add_argument(
            "--compressed-title",
            type=str,
            default="column_compressed",
            help="Title for the compressed column.",
        )
        self.arg_parser.add_argument(
            "--interval-length",
            type=int,
            action="append",
            help="Length of the interval for compression.",
        )
        self.arg_parser.add_argument(
            "--hadamard-order",
            type=int,
            default=None,
            help="Order of the Hadamard construction method.",
        )
        self.arg_parser.add_argument(
            "--number-of-decoys",
            type=int,
            default=0,
            help="Number of decoy rows to add to the table.",
        )

    def parse_args(self):
        """
        Parses the command line arguments.
        """
        return self.arg_parser.parse_args()
