from backend.utils.custom_exception import CustomException


class TestCustomException:
    def test_basic_exception_message(self):
        exc = CustomException("test error")
        assert str(exc) == "test error"

    def test_exception_with_detail(self):
        try:
            raise ValueError("inner")
        except ValueError as e:
            exc = CustomException("outer", e)
            assert "outer" in str(exc)
            assert "test_custom_exception" in str(exc)

    def test_exception_is_exception_subclass(self):
        exc = CustomException("error")
        assert isinstance(exc, Exception)
