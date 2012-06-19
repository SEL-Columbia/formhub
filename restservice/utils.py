from odk_logger.models.instance import Instance
from restservice.models import RestService

def call_service(instance):
    print "call_service has been called!"
    # lookup service
    if isinstance(instance, Instance):
        # registered services
        services = RestService.objects.filter(xform=instance.xform)
        print services
        # call service send with url and data parameters
        for sv in services:
            m = __import__(''.join(['restservice.services.', sv.name]), globals(),locals(), ['ServiceDefinition'])
            print m.ServiceDefinition;
            # TODO: Queue service
            service = m.ServiceDefinition()
            service.send(sv.service_url, instance)
