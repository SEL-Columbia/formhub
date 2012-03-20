from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User

from odk_viewer.models import ParsedInstance
from utils.model_tools import queryset_iterator

class Command(BaseCommand):
    help = "Insert all existing parsed instances into MongoDB"

    def handle(self, *args, **kwargs):
        message = kwargs['message']
        if not message:
            raise AttributeError('message must be included in kwargs')
        # get all users
        #users = User.objects.all()
        # TODO uncomment above and remove below after testing
        users = User.objects.filter(pk__in=[7,91,159])
        for user in users:
            # send each email separately so users cannot see eachother
            send_templated_mail(
                template_name='notice',
                from_email='noreply@formhub.org',
                recipient_list=[user.email],
                context={
                    'username':user.username,
                    'full_name':user.get_full_name(),
                    'message': message
                },
            )
