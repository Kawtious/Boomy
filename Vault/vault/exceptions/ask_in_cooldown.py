class AskInCooldown(Exception):
    def __init__(self, message="Ask in cooldown", cooldown: float = 0):
        super().__init__(message)
        self.cooldown = cooldown
