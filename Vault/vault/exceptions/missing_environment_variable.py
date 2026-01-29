class MissingEnvironmentVariable(Exception):
    def __init__(self, variable):
        super().__init__(f"Missing environment variable: {variable}")
