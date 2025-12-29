from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.dependencies import (
    get_access_token,
    get_current_user,
    get_itinerary_store,
    get_orchestrator,
)
from app.main import create_app
from app.schemas.auth import AuthenticatedUser
from app.schemas.itineraries import SavedItineraryDetail, SavedItinerarySummary
from app.schemas.trips import PlannedTripResult, TripPlanData, TripPlanMeta


class StubItineraryStore:
    def __init__(self) -> None:
        self.saved_payload = None
        self.saved_edit = None
        self.restored_version = None
        self.deleted_itinerary_id = None
        self.saved_trip = {
            "id": "trip-1",
            "destination": "Bangkok",
            "number_of_days": 3,
            "trip_start": "2026-04-01",
            "itinerary_type": "Adventure",
            "budget": "Medium",
            "title": "Bangkok Escape",
            "summary": "A balanced city trip with temples, food, and evening markets.",
            "status": "saved",
            "current_version": 1,
            "created_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
            "trip_request": {
                "destination": "Bangkok",
                "number_of_days": 3,
                "trip_start": "2026-04-01",
                "itinerary_type": "Adventure",
                "budget": "Medium",
            },
            "current_itinerary": {
                "itinerary": [
                    {
                        "day": "Day 1",
                        "activities": [
                            {
                                "time": "09:00 AM",
                                "name": "Wat Arun",
                                "location": "Bangkok",
                                "price": 15,
                                "duration": "2 hours",
                                "description": "Start the trip with a riverside temple visit.",
                            }
                        ],
                    }
                ]
            },
            "messages": [
                {
                    "role": "assistant",
                    "content": "Draft itinerary ready.",
                    "created_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
                }
            ],
            "versions": [
                {
                    "version_number": 1,
                    "created_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
                }
            ],
        }

    async def create_itinerary(self, *, user, access_token: str, payload):
        self.saved_payload = {
            "user": user,
            "access_token": access_token,
            "payload": payload,
        }
        return SavedItineraryDetail.model_validate(self.saved_trip)

    async def list_itineraries(self, *, user, access_token: str):
        return [
            SavedItinerarySummary.model_validate(
                {
                    key: self.saved_trip[key]
                    for key in [
                        "id",
                        "destination",
                        "number_of_days",
                        "trip_start",
                        "itinerary_type",
                        "budget",
                        "title",
                        "summary",
                        "status",
                        "current_version",
                        "created_at",
                        "updated_at",
                    ]
                }
            )
        ]

    async def get_itinerary(self, *, user, access_token: str, itinerary_id: str):
        if itinerary_id != self.saved_trip["id"]:
            return None
        return SavedItineraryDetail.model_validate(self.saved_trip)

    async def save_edit(
        self,
        *,
        user,
        access_token: str,
        itinerary_id: str,
        message: str,
        updated_itinerary,
    ):
        self.saved_edit = {
            "user": user,
            "access_token": access_token,
            "itinerary_id": itinerary_id,
            "message": message,
            "updated_itinerary": updated_itinerary,
        }
        edited_trip = dict(self.saved_trip)
        edited_trip["current_version"] = 2
        edited_trip["versions"] = [
            {
                "version_number": 2,
                "created_at": datetime(2026, 4, 2, tzinfo=timezone.utc),
            },
            *self.saved_trip["versions"],
        ]
        edited_trip["messages"] = [
            *self.saved_trip["messages"],
            {
                    "role": "user",
                    "content": message,
                    "created_at": datetime(2026, 4, 2, tzinfo=timezone.utc),
                },
            ]
        edited_trip["current_itinerary"] = {
            "itinerary": [
                {
                    "day": "Day 1",
                    "activities": [
                        {
                            "time": "09:00 AM",
                            "name": "Wat Arun",
                            "location": "Bangkok",
                            "price": 15,
                            "duration": "2 hours",
                            "description": "Start the trip with a riverside temple visit.",
                        },
                        {
                            "time": "07:00 PM",
                            "name": "Night market",
                            "location": "Bangkok",
                            "price": 12,
                            "duration": "2 hours",
                            "description": "Street food and shopping.",
                        },
                    ],
                }
            ]
        }
        return SavedItineraryDetail.model_validate(edited_trip)

    async def delete_itinerary(self, *, user, access_token: str, itinerary_id: str):
        self.deleted_itinerary_id = itinerary_id
        return itinerary_id == self.saved_trip["id"]

    async def restore_version(
        self,
        *,
        user,
        access_token: str,
        itinerary_id: str,
        version_number: int,
    ):
        if itinerary_id != self.saved_trip["id"]:
            from app.services.itinerary_store import ItineraryStoreError

            raise ItineraryStoreError(
                user_message="We couldn't find that saved itinerary.",
                status_code=404,
            )
        if version_number != 1:
            from app.services.itinerary_store import ItineraryStoreError

            raise ItineraryStoreError(
                user_message="We couldn't find that saved version.",
                status_code=404,
            )

        self.restored_version = version_number
        restored_trip = dict(self.saved_trip)
        restored_trip["current_version"] = 2
        restored_trip["versions"] = [
            {
                "version_number": 2,
                "created_at": datetime(2026, 4, 2, tzinfo=timezone.utc),
            },
            *self.saved_trip["versions"],
        ]
        restored_trip["messages"] = [
            *self.saved_trip["messages"],
            {
                "role": "user",
                "content": "Restore version 1",
                "created_at": datetime(2026, 4, 2, tzinfo=timezone.utc),
            },
            {
                "role": "assistant",
                "content": "Restored the itinerary to version 1 and saved it as version 2.",
                "created_at": datetime(2026, 4, 2, tzinfo=timezone.utc),
            },
        ]
        return SavedItineraryDetail.model_validate(restored_trip)

    async def get_version_preview(
        self,
        *,
        user,
        access_token: str,
        itinerary_id: str,
        version_number: int,
    ):
        if itinerary_id != self.saved_trip["id"]:
            from app.services.itinerary_store import ItineraryStoreError

            raise ItineraryStoreError(
                user_message="We couldn't find that saved itinerary.",
                status_code=404,
            )
        if version_number != 1:
            from app.services.itinerary_store import ItineraryStoreError

            raise ItineraryStoreError(
                user_message="We couldn't find that saved version.",
                status_code=404,
            )

        return {
            "itinerary_id": itinerary_id,
            "version_number": 1,
            "created_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
            "itinerary": self.saved_trip["current_itinerary"],
        }


class StubSavedEditOrchestrator:
    provider_names = ["gemini"]

    async def edit_trip(self, request):
        return PlannedTripResult(
            data=TripPlanData(
                itinerary=[
                    {
                        "day": "Day 1",
                        "activities": [
                            {
                                "time": "09:00 AM",
                                "name": "Wat Arun",
                                "location": "Bangkok",
                                "price": 15,
                                "duration": "2 hours",
                                "description": "Start the trip with a riverside temple visit.",
                            },
                            {
                                "time": "07:00 PM",
                                "name": "Night market",
                                "location": "Bangkok",
                                "price": 12,
                                "duration": "2 hours",
                                "description": "Street food and shopping.",
                            },
                        ],
                    }
                ]
            ),
            meta=TripPlanMeta(
                provider="gemini",
                model="gemini-2.5-flash",
                attempted_providers=["gemini"],
            ),
        )


def _authed_client(store: StubItineraryStore) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id="user-123",
        email="traveler@example.com",
    )
    app.dependency_overrides[get_access_token] = lambda: "test-access-token"
    app.dependency_overrides[get_itinerary_store] = lambda: store
    app.dependency_overrides[get_orchestrator] = lambda: StubSavedEditOrchestrator()
    return TestClient(app)


def test_create_saved_itinerary_requires_auth() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/itineraries",
        json={
            "trip_request": {
                "destination": "Bangkok",
                "number_of_days": 3,
                "trip_start": "2026-04-01",
                "itinerary_type": "Adventure",
                "budget": "Medium",
            },
            "current_itinerary": {
                "itinerary": [
                    {
                        "day": "Day 1",
                        "activities": [
                            {
                                "time": "09:00 AM",
                                "name": "Wat Arun",
                                "location": "Bangkok",
                                "price": 15,
                                "duration": "2 hours",
                                "description": "Start the trip with a riverside temple visit.",
                            }
                        ],
                    }
                ]
            },
            "client_request_id": "draft-request-1",
        },
    )

    assert response.status_code == 401


def test_create_saved_itinerary_returns_saved_trip() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.post(
        "/api/itineraries",
        json={
            "trip_request": {
                "destination": "Bangkok",
                "number_of_days": 3,
                "trip_start": "2026-04-01",
                "itinerary_type": "Adventure",
                "budget": "Medium",
            },
            "current_itinerary": {
                "itinerary": [
                    {
                        "day": "Day 1",
                        "activities": [
                            {
                                "time": "09:00 AM",
                                "name": "Wat Arun",
                                "location": "Bangkok",
                                "price": 15,
                                "duration": "2 hours",
                                "description": "Start the trip with a riverside temple visit.",
                            }
                        ],
                    }
                ]
            },
            "messages": [
                {
                    "role": "assistant",
                    "content": "Draft itinerary ready.",
                }
            ],
            "client_request_id": "draft-request-1",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["id"] == "trip-1"
    assert store.saved_payload["user"].email == "traveler@example.com"
    assert store.saved_payload["payload"].client_request_id == "draft-request-1"


def test_list_saved_itineraries_returns_user_trips() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.get("/api/itineraries")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"][0]["destination"] == "Bangkok"


def test_get_saved_itinerary_returns_detail() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.get("/api/itineraries/trip-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["current_itinerary"]["itinerary"][0]["day"] == "Day 1"
    assert payload["data"]["messages"][0]["content"] == "Draft itinerary ready."
    assert payload["data"]["versions"][0]["version_number"] == 1


def test_get_missing_saved_itinerary_returns_not_found_envelope() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.get("/api/itineraries/missing-trip")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"] == "Saved itinerary not found."


def test_edit_saved_itinerary_returns_new_version() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.post(
        "/api/itineraries/trip-1/edit",
        json={
            "message": "Add an evening market stop",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["current_version"] == 2
    assert payload["data"]["versions"][0]["version_number"] == 2
    assert (
        payload["data"]["current_itinerary"]["itinerary"][0]["activities"][-1]["name"]
        == "Night market"
    )
    assert store.saved_edit["message"] == "Add an evening market stop"


def test_delete_saved_itinerary_returns_success() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.delete("/api/itineraries/trip-1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["deleted"] is True
    assert store.deleted_itinerary_id == "trip-1"


def test_delete_missing_saved_itinerary_returns_not_found_envelope() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.delete("/api/itineraries/missing-trip")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"] == "Saved itinerary not found."


def test_restore_saved_itinerary_version_returns_new_current_version() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.post("/api/itineraries/trip-1/versions/1/restore")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["current_version"] == 2
    assert payload["data"]["versions"][0]["version_number"] == 2
    assert store.restored_version == 1


def test_restore_missing_saved_itinerary_version_returns_not_found_envelope() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.post("/api/itineraries/trip-1/versions/99/restore")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"] == "We couldn't find that saved version."


def test_get_saved_itinerary_version_preview_returns_version_payload() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.get("/api/itineraries/trip-1/versions/1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["version_number"] == 1
    assert payload["data"]["itinerary"]["itinerary"][0]["day"] == "Day 1"


def test_get_missing_saved_itinerary_version_preview_returns_not_found_envelope() -> None:
    store = StubItineraryStore()
    client = _authed_client(store)

    response = client.get("/api/itineraries/trip-1/versions/99")

    assert response.status_code == 404
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"] == "We couldn't find that saved version."
