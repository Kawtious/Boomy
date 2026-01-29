class InvalidEnvironmentVariable(Exception):
    def __init__(self, variable, reason=None):
        if reason:
            variable += f" {reason}"

        super().__init__(f"Invalid environment variable: {variable}")
