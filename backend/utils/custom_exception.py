class CustomException(Exception):
    def __init__(self, error_message: str, error_detail: Exception | None = None):
        super().__init__(error_message)
        self.error_message = self._get_detailed_error_message(error_message, error_detail)

    @staticmethod
    def _get_detailed_error_message(error_message: str, error_detail: Exception | None) -> str:
        if error_detail and error_detail.__traceback__:
            tb = error_detail.__traceback__
            while tb.tb_next:
                tb = tb.tb_next
            file_name = tb.tb_frame.f_code.co_filename
            line_no = tb.tb_lineno
            return f"Error in {file_name}, line {line_no}: {error_message}"
        return error_message

    def __str__(self) -> str:
        return self.error_message
