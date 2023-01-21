from typing import Any

import boto3

REGION_NAME = "eu-west-3"
ME_EMAIL = "ntoussai29@gmail.com"

SES_CLIENT = Any


def build_client_email() -> SES_CLIENT:
    client = boto3.client("ses", region_name=REGION_NAME)
    return client


def send_text_email(
    client: SES_CLIENT, author: str, to: str, title: str, text: str
) -> None:
    response = client.send_email(
        Source=author,
        Destination={
            "ToAddresses": [
                to,
            ],
        },
        Message={
            "Subject": {
                "Data": title,
            },
            "Body": {
                "Text": {
                    "Data": text,
                },
                "Html": {
                    "Data": text,
                },
            },
        },
    )


def send_me_email_with_text(client: SES_CLIENT, title: str, text: str) -> None:
    send_text_email(client, ME_EMAIL, ME_EMAIL, title, text)


def create_client_and_send_me_email_with_text(title: str, text: str) -> None:
    client = build_client_email()
    send_me_email_with_text(client, title, text)
