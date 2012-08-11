from django.core.management.base import BaseCommand
from django.test.simple import DjangoTestSuiteRunner
from django.utils.translation import ugettext_lazy


class Command(BaseCommand):
    help = ugettext_lazy("""
    Run the tests locally. If there are no errors push to
    develop, and update the staging server. (This should probably
    update the develop server)
    """)

    def handle(self, *args, **kwargs):
        runner = DjangoTestSuiteRunner()
        number_failed_tests = runner.run_tests(None)
        if number_failed_tests==0:
            print "yay"
            # run('git push origin develop')
            # deploy_staging()    

