from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.http import HttpRequest
from django.test import override_settings
from django.urls import reverse
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.test import APITestCase

from openforms.accounts.tests.factories import SuperUserFactory, TokenFactory
from openforms.tests.utils import NOOP_CACHES
from openforms.variables.constants import FormVariableSources
from openforms.variables.tests.factories import ServiceFetchConfigurationFactory

from ..models import Form, FormDefinition, FormStep, FormVariable
from .factories import (
    FormDefinitionFactory,
    FormFactory,
    FormLogicFactory,
    FormStepFactory,
    FormVariableFactory,
)


class CopyFormAPITests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="john", password="secret", email="john@example.com"
        )
        self.token = TokenFactory(user=self.user)

    @override_settings(CACHES=NOOP_CACHES)
    def test_form_copy_with_reusable_definition(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(is_reusable=True)
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)

        url = reverse("api:form-copy", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        copied_form = Form.objects.last()
        copied_form_step = copied_form.formstep_set.first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(response.json()["uuid"], str(copied_form.uuid))
        self.assertEqual(response.json()["name"], copied_form.name)
        self.assertEqual(response.json()["loginRequired"], copied_form.login_required)
        self.assertEqual(response.json()["product"], copied_form.product)
        self.assertEqual(response.json()["slug"], copied_form.slug)
        self.assertEqual(
            response.json()["steps"][0]["uuid"], str(copied_form_step.uuid)
        )
        self.assertEqual(
            response.json()["steps"][0]["formDefinition"],
            copied_form_step.form_definition.name,
        )

        self.assertEqual(Form.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 1)
        self.assertEqual(FormStep.objects.count(), 2)

        self.assertIn(
            reverse("api:form-detail", kwargs={"uuid_or_slug": copied_form.uuid}),
            response["Location"],
        )

        self.assertNotEqual(copied_form.pk, form.pk)
        self.assertNotEqual(copied_form.uuid, str(form.uuid))
        self.assertEqual(copied_form.active, form.active)
        self.assertEqual(copied_form.registration_backend, form.registration_backend)
        self.assertEqual(copied_form.name, _("{name} (copy)").format(name=form.name))
        self.assertIsNone(copied_form.product)
        self.assertEqual(copied_form.slug, _("{slug}-copy").format(slug=form.slug))

        self.assertNotEqual(copied_form_step.pk, form_step.pk)
        self.assertNotEqual(copied_form_step.uuid, str(form_step.uuid))
        self.assertEqual(copied_form_step.form.pk, copied_form.pk)
        self.assertEqual(copied_form_step.order, form_step.order)

    @override_settings(CACHES=NOOP_CACHES)
    def test_form_copy_with_non_reusable_definition(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        form = FormFactory.create()
        form_definition = FormDefinitionFactory.create(is_reusable=False)
        form_step = FormStepFactory.create(form=form, form_definition=form_definition)

        url = reverse("api:form-copy", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        copied_form = Form.objects.exclude(uuid=form.uuid).get()
        copied_form_step = copied_form.formstep_set.first()

        self.assertEqual(Form.objects.count(), 2)
        self.assertEqual(FormDefinition.objects.count(), 2)
        self.assertEqual(FormStep.objects.count(), 2)

        self.assertIn(
            reverse("api:form-detail", kwargs={"uuid_or_slug": copied_form.uuid}),
            response["Location"],
        )

        self.assertNotEqual(copied_form_step.form_definition, form_step.form_definition)

    def test_form_copy_already_exists(self):
        self.user.user_permissions.add(Permission.objects.get(codename="change_form"))
        self.user.is_staff = True
        self.user.save()

        form = FormFactory.create()

        url = reverse("api:form-copy", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(
            response.json()["name"], _("{name} (copy)").format(name=form.name)
        )
        self.assertEqual(
            response.json()["slug"], _("{slug}-copy").format(slug=form.slug)
        )

        copy_form_slug = response.json()["slug"]

        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(
            response.json()["name"], _("{name} (copy)").format(name=form.name)
        )
        self.assertEqual(response.json()["slug"], "{}-2".format(copy_form_slug))

        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.has_header("Location"))
        self.assertEqual(
            response.json()["name"], _("{name} (copy)").format(name=form.name)
        )
        self.assertEqual(response.json()["slug"], "{}-3".format(copy_form_slug))

    def test_form_copy_token_auth_required(self):
        form = FormFactory.create()
        url = reverse("api:form-copy", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_copy_session_auth_not_allowed(self):
        self.user.is_staff = True
        self.user.save()

        self.client.login(
            request=HttpRequest(), username=self.user.username, password="secret"
        )

        form = FormFactory.create()
        url = reverse("api:form-copy", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_form_copy_staff_required(self):
        self.user.is_staff = False
        self.user.save()

        form = FormFactory.create()
        url = reverse("api:form-copy", kwargs={"uuid_or_slug": form.uuid})
        response = self.client.post(
            url,
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CopyFormWithVarsTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        user = SuperUserFactory.create()
        cls.user = user
        cls.token = TokenFactory(user=user)

    def test_copy_form_with_variables(self):
        form: Form = FormFactory.create(slug="test-copying-with-vars")
        FormStepFactory.create(
            form=form,
            form_definition__configuration={
                "components": [
                    {
                        "type": "textfield",
                        "key": "name",
                    },
                    {
                        "type": "textfield",
                        "key": "surname",
                    },
                ]
            },
        )
        FormVariableFactory.create(
            form=form,
            source=FormVariableSources.user_defined,
            key="bla",
            service_fetch_configuration=ServiceFetchConfigurationFactory.create(),
        )
        FormLogicFactory.create(
            form=form,
            json_logic_trigger={"!": {"var": "bla"}},
            is_advanced=True,
            actions=[
                {
                    "action": {"type": "fetch-from-service", "value": ""},
                    "variable": "bla",
                }
            ],
        )

        self.assertEqual(1, Form.objects.count())
        self.assertEqual(3, FormVariable.objects.filter(form=form).count())
        self.assertEqual(form.formlogic_set.count(), 1)

        url = reverse("api:form-copy", args=(form.uuid,))
        response = self.client.post(
            url, format="json", HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.assertEqual(status.HTTP_201_CREATED, response.status_code)

        forms = Form.objects.all()

        self.assertEqual(2, forms.count())

        form_copy = forms.get(~Q(slug__in=["test-copying-with-vars"]))
        variables_copy = form_copy.formvariable_set.all()

        self.assertEqual(3, variables_copy.count())
        self.assertEqual(
            2, variables_copy.filter(source=FormVariableSources.component).count()
        )
        self.assertEqual(
            1, variables_copy.filter(source=FormVariableSources.user_defined).count()
        )
        self.assertEqual(form_copy.formlogic_set.count(), 1)
