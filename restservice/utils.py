from odk_logger.models.instance import Instance
from restservice.models import RestService

def call_service(instance):
    print "call_service has been called!"
    # lookup service
    if isinstance(instance, Instance):
        # registered services
        services = RestService.objects.filter(xform=instance.xform)
        # call service send with url and data parameters
        for sv in services:
            # TODO: Queue service
            service = sv.get_service_definition()()
            service.send(sv.service_url, instance)
