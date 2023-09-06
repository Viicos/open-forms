import factory

from openforms.registrations.contrib.zgw_apis.tests.factories import ServiceFactory

from ..models import ServiceFetchConfiguration


class ServiceFetchConfigurationFactory(factory.django.DjangoModelFactory):
    service = factory.SubFactory(ServiceFactory)
    name = factory.Sequence(lambda n: f"Service Fetch Config #{n}")

    class Meta:
        model = ServiceFetchConfiguration
