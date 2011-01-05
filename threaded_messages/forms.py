import datetime
from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.contrib.auth.models import User

from django_messages.models import *
from django_messages.fields import CommaSeparatedUserField


class ComposeForm(forms.Form):
    """
    A form for creating a new message thread to one or more users.
    """
    recipient = CommaSeparatedUserField(label=_(u"Recipient"))
    subject = forms.CharField(label=_(u"Subject"))
    body = forms.CharField(label=_(u"Body"),
        widget=forms.Textarea(attrs={'rows': '12', 'cols':'55'}))
    
    def __init__(self, sender, *args, **kwargs):
        recipient_filter = kwargs.pop('recipient_filter', None)
        super(ComposeForm, self).__init__(*args, **kwargs)
        if recipient_filter is not None:
            self.fields['recipient']._recipient_filter = recipient_filter
        self.sender = sender
    
    def save(self):
        recipients = self.cleaned_data['recipient']
        subject = self.cleaned_data['subject']
        body = self.cleaned_data['body']
        
        new_message = Message.objects.create(body=body, sender=self.sender)
        
        thread = Thread.objects.create(subject=subject,
                                       latest_msg=new_message)
        thread.all_msgs.add(new_message)
        thread.save()

        for recipient in recipients:
            if recipient != self.sender:
                Participant.objects.create(thread=thread, user=recipient)
        
        (sender_part, created) = Participant.objects.get_or_create(thread=thread, user=self.sender)
        sender_part.replied_at = sender_part.read_at = datetime.datetime.now()
        sender_part.save()
        
        return thread

class ReplyForm(forms.Form):
    """
    A simpler form used for the replies.
    """
    body = forms.CharField(label=_(u"Reply"),
        widget=forms.Textarea(attrs={'rows': '4', 'cols':'55'}))
    
    def save(self, sender, thread):
        body = self.cleaned_data['body']
        
        new_message = Message.objects.create(body=body, sender=sender)
        new_message.parent_msg = thread.latest_msg
        thread.latest_msg = new_message
        thread.all_msgs.add(new_message)
        thread.save()
        new_message.save()
        
        for participant in thread.participants.all():
            participant.deleted_at = None
            participant.save()
        
        sender_part = Participant.objects.get(thread=thread, user=sender)
        sender_part.replied_at = sender_part.read_at = datetime.datetime.now()
        sender_part.save()
        
        return thread
