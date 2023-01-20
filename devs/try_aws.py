#%%
import boto3

# %%
client = boto3.client("ses", region_name="eu-west-3")

# %%
response = client.verify_email_identity(EmailAddress="ntoussai29@gmail.com")
print(response)
# %%
response = client.send_email(
    Source="toto@gmail.com",
    Destination={
        "ToAddresses": [
            "ntoussai29@gmail.com",
        ],
    },
    Message={
        "Subject": {
            "Data": "Premier mail depuis SES",
        },
        "Body": {
            "Text": {
                "Data": "AWS ecrit ce message",
            },
            "Html": {
                "Data": "AWS ecrit ce message",
            },
        },
    },
)
