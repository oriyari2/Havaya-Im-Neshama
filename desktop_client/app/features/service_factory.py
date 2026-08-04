from __future__ import annotations

from desktop_client.app.features.activities.service import ActivityService
from desktop_client.app.features.ai_assistant.service import AIChatService
from desktop_client.app.features.bookings.assignment_service import AssignmentService
from desktop_client.app.features.bookings.service import BookingService
from desktop_client.app.features.contracts import FeatureServices
from desktop_client.app.features.customers.service import CustomerService
from desktop_client.app.features.instructors.service import InstructorService
from desktop_client.app.features.knowledge.service import KnowledgeService
from desktop_client.app.features.users.service import UserService


def build_feature_services(api_client) -> FeatureServices:
    """Create the shared service instances consumed by mounted feature packages."""

    return FeatureServices(
        booking=BookingService(api_client),
        assignment=AssignmentService(api_client),
        activity=ActivityService(api_client),
        ai_chat=AIChatService(api_client),
        customer=CustomerService(api_client),
        instructor=InstructorService(api_client),
        knowledge=KnowledgeService(api_client),
        user=UserService(api_client),
    )
