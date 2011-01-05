import django.dispatch

threaded_message_sent = django.dispatch.Signal(providing_args=["message"])