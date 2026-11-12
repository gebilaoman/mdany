"""mdany: convert a set of Markdown documents into a PDF / DOCX submission package."""

__version__ = "0.1.0.dev0"


class MdanyError(Exception):
    """An error that the CLI reports to the user without a traceback."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code
