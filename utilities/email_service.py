from flask import render_template, current_app
from threading import Thread
from flask_mail import Message

from exts import mail


class EmailService:
    """ "A service for sending emails using Flask-Mail"""

    @staticmethod
    def send_async_email(app, msg):
        with app.app_context():
            mail.send(msg)

    @staticmethod
    def send_mail(subject, recipients, body, html=None, sender=None):
        """ "Send basic email"""
        app = current_app._get_current_object()
        msg = Message(
            subject=subject,
            sender=sender or app.config.get("MAIL_DEFAULT_SENDER"),
            recipients=recipients if isinstance(recipients, list) else [recipients],
            body=body,
            html=html,
        )
        Thread(target=EmailService.send_async_email, args=(app, msg)).start()

    @staticmethod
    def send_template_email(
        subject, body, recipients, template, context=None, sender=None
    ):
        """Send email using a template"""
        app = current_app._get_current_object()
        context = context or {}

        html = render_template(template, **context)

        if not body:
            try:
                text_template = template.replace(".html", ".txt")
                body = render_template(text_template, **context)
            except Exception:
                body = EmailService._html_to_text(html)

        EmailService.send_mail(subject, recipients, body, html, sender)
