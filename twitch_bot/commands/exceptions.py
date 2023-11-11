class CommandOnCooldown(Exception):
    def __init__(self, retry_after: float) -> None:
        super().__init__(f"Command is on cooldown for {retry_after}s")
        self.retry_after = retry_after
