class OrdersError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        if self.message:
            return f"Orders application error with message: '{self.message}' has been raised"
        else:
            return "Orders application error without message has been raised"


class BusinessError(Exception):
    def __init__(self, message):
        super().__init__(message)
