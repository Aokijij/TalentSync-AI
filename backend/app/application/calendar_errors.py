class CalendarProviderError(Exception):
    def __init__(self, code="temporary"):
        self.code = code
        super().__init__("Calendar provider operation failed")
