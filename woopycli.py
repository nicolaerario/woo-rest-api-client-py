import csv
from datetime import date

import requests
import typer
from environs import Env
from woocommerce import API

cli = typer.Typer()


env = Env()
env.read_env()

wcapi = API(
    url=env.str("URL"),
    consumer_key=env.str("CONSUMER_KEY"),
    consumer_secret=env.str("CONSUMER_SECRET"),
    timeout=20,
)


defaultDate = date.today().strftime("%Y-%m-%dT00:00:00")


@cli.command()
def status():
    """Show some server infos."""

    response = wcapi.get("system_status").json()

    woo_version = response["environment"]["version"]
    wp_version = response["environment"]["wp_version"]
    php_version = response["environment"]["php_version"]
    remote_get_successful = response["environment"]["remote_get_successful"]

    typer.echo(
        f"""
    Woocommerce version:    {woo_version}
    Wordpress version:      {wp_version}
    PHP version:            {php_version}
    Get Request:            {'OK' if remote_get_successful else 'BAD'}
    """
    )


@cli.command()
def shipToCsv(date: str = defaultDate, status: str = "processing"):
    """
    Export shippings with contact details to a CSV file.

    --date : limit response to resources published after a given ISO8601 compliant date (yyyy-mm-ddThh:mm:ss).
    Default is today at midnight.

    --status : limit result set to orders assigned a specific status.
     Options: any, pending, processing, on-hold, completed, cancelled, refunded, failed and trash. Default is processing.
    """

    try:

        response = wcapi.get(
            "orders", params={"after": f"{date}", "status": f"{status}"}
        )

        # Set the csv header structure
        header = [
            "Order Number",
            "First Name",
            "Last Name",
            "Company",
            "Address 1",
            "Address 2",
            "City",
            "State",
            "Postcode",
            "Country",
            "E-mail",
            "Phone",
        ]

        # Extract needed details from the raw response
        details = [
            (
                obj["number"],
                obj["shipping"]["first_name"],
                obj["shipping"]["last_name"],
                obj["shipping"]["company"],
                obj["shipping"]["address_1"],
                obj["shipping"]["address_2"],
                obj["shipping"]["city"],
                obj["shipping"]["state"],
                obj["shipping"]["postcode"],
                obj["shipping"]["country"],
                obj["billing"]["email"],
                obj["billing"]["phone"],
            )
            for obj in response.json()
        ]

        # Export the result to csv file
        with open("shippings.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            writer.writerows(details)

    except requests.exceptions.RequestException as error:
        typer.echo(f"Oopss: {error}")
        raise typer.Abort()

    else:
        # Print the success message
        typer.echo(f"{status.title()} orders after {date} downloaded!")


if __name__ == "__main__":
    cli()
