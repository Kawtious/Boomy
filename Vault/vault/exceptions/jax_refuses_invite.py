class JaxRefusesInvite(Exception):
    def __init__(self, message="Jax refuses invite"):
        super().__init__(message)
