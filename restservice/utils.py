from restservice.models import RestService


def call_service(parsed_instance):
    # lookup service
    instance = parsed_instance.instance
    services = RestService.objects.filter(xform=instance.xform)
    # call service send with url and data parameters
    for sv in services:
        # TODO: Queue service
        try:
            service = sv.get_service_definition()()
            service.send(sv.service_url, parsed_instance)
        except:
            # TODO: Handle gracefully | requeue/resend
            pass
