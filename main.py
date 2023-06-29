from src.client import Client
import logging

logging.basicConfig(
    filename="client.log",
    level=logging.ERROR,
    format="%(levelname)s:%(asctime)s:%(message)s",
)


def main():
    settings = Client.load_settings()
    client = Client(
        token=settings["token"],
        prefix=settings["prefix"],
        initial_channels=settings["initial_channels"],
    )
    client.add_cogs(settings["cogs"])
    client.run()


if __name__ == "__main__":
    main()
