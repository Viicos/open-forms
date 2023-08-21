from django.test import TestCase, override_settings
from django.urls import reverse

from dateutil.parser import isoparse

from openforms.submissions.tests.factories import SubmissionFactory

from ..base import (
    AppointmentDetails,
    AppointmentLocation,
    AppointmentProduct,
    BasePlugin,
)
from ..tokens import submission_appointment_token_generator
from .factories import AppointmentInfoFactory


class TestPlugin(BasePlugin):
    def get_appointment_details(self, identifier: str) -> str:
        return AppointmentDetails(
            identifier=identifier,
            products=[
                AppointmentProduct(identifier="1", name="Test product 1"),
                AppointmentProduct(identifier="2", name="Test product 2"),
            ],
            location=AppointmentLocation(identifier="1", name="Test location"),
            start_at=isoparse("2021-01-01T11:00:00+00:00"),
            end_at=isoparse("2021-01-01T11:15+00:00"),
            remarks="Remarks",
            other={"Some": "<h1>Data</h1>"},
        )


class BasePluginTests(TestCase):
    maxDiff = 1024

    @classmethod
    def setUpTestData(cls):
        cls.plugin = TestPlugin("base")

    @override_settings(BASE_URL="https://example.com/")
    def test_get_cancel_link(self):
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(submission=submission, registration_ok=True)

        result = self.plugin.get_cancel_link(submission)

        cancel_path = reverse(
            "appointments:appointments-verify-cancel-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )
        cancel_url = f"https://example.com{cancel_path}"
        self.assertEqual(cancel_url, result)

    @override_settings(BASE_URL="https://example.com/")
    def test_get_change_link(self):
        submission = SubmissionFactory.create(completed=True)
        AppointmentInfoFactory.create(submission=submission, registration_ok=True)

        result = self.plugin.get_change_link(submission)

        change_path = reverse(
            "appointments:appointments-verify-change-appointment-link",
            kwargs={
                "token": submission_appointment_token_generator.make_token(submission),
                "submission_uuid": submission.uuid,
            },
        )
        change_url = f"https://example.com{change_path}"
        self.assertEqual(change_url, result)
