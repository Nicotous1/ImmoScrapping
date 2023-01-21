from immo_scrap import aws


def lambda_handler(event, context):
    aws.create_client_and_send_me_email_with_text("Titre", "Text :)")
