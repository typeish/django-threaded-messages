# -*- coding:utf-8 -*-
import re

from django.conf import settings
from django.contrib.sites.models import Site
from django.template.loader import render_to_string

# favour django-mailer but fall back to django.core.mail
if "mailer" in settings.INSTALLED_APPS:
    from mailer import send_mail
else:
    from django.core.mail import send_mail

def message_email_notification( message,
                                template_name="django_messages/new_message.html",
                                default_protocol=None,
                                subject_prefix="New message from %s on %s: %s",
                                *args, **kwargs):
    """
    This function sends an email and is called via Django's signal framework.
    Optional arguments:
        ``template_name``: the template to use
        ``subject_prefix``: prefix for the email subject.
        ``default_protocol``: default protocol in site URL passed to template
    """

    if default_protocol is None:
        default_protocol = getattr(settings, 'DEFAULT_HTTP_PROTOCOL', 'http')
    
    try:
        thread = message.thread.all()[0]
        current_domain = Site.objects.get_current().domain
        subject = subject_prefix % (message.sender.username, current_domain, thread.subject)
        email_message = render_to_string(template_name, {
            'site_url': '%s://%s' % (default_protocol, current_domain),
            'site_name': current_domain,
            'message': message,
        })
        recipients = []
        for p in thread.participants.exclude(user=message.sender):
            if p.user.email:
                recipients.append(p.user.email)
        if recipients:
            send_mail(subject, email_message, settings.DEFAULT_FROM_EMAIL, recipients)
    except Exception, e:
        # print e
        pass #fail silently
