from immo_scrap import analysis, aws


def send_analysis_if_sold_or_new(analysis: analysis.GlobalAnalysis) -> None:
    if analysis.has_evolved:
        send_analysis(analysis)


def format_text_for_mail_html(s: str) -> str:
    return s.replace("\n", "<br>").replace(
        "\t", "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
    )


def send_analysis(to_send: analysis.GlobalAnalysis) -> None:
    print("Sending mail")
    title = analysis.format_GlobalAnalysis_title(to_send)
    text = analysis.format_GlobalAnalysis_text(to_send)
    text_formatted = format_text_for_mail_html(text)
    aws.create_client_and_send_me_email_with_text(title, text_formatted)
