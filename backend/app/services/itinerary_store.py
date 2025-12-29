import asyncio
from dataclasses import dataclass
from datetime import date, datetime, timezone

from supabase import Client, create_client
from supabase.client import ClientOptions

from app.schemas.auth import AuthenticatedUser
from app.schemas.itineraries import (
    SavedItineraryDetail,
    SavedItineraryMessage,
    SavedItinerarySummary,
    SavedItineraryVersion,
    SavedItineraryVersionPreview,
    SaveItineraryRequest,
)
from app.schemas.trips import TripPlanData, TripPlanRequest


@dataclass(frozen=True)
class ItineraryStoreError(Exception):
    user_message: str
    status_code: int


class SupabaseItineraryStore:
    def __init__(self, supabase_url: str | None, supabase_anon_key: str | None):
        self._supabase_url = supabase_url
        self._supabase_anon_key = supabase_anon_key

    @property
    def is_configured(self) -> bool:
        return bool(self._supabase_url and self._supabase_anon_key)

    async def create_itinerary(
        self,
        *,
        user: AuthenticatedUser,
        access_token: str,
        payload: SaveItineraryRequest,
    ) -> SavedItineraryDetail:
        return await asyncio.to_thread(
            self._create_itinerary_sync,
            user,
            access_token,
            payload,
        )

    async def list_itineraries(
        self,
        *,
        user: AuthenticatedUser,
        access_token: str,
    ) -> list[SavedItinerarySummary]:
        return await asyncio.to_thread(
            self._list_itineraries_sync,
            user,
            access_token,
        )

    async def get_itinerary(
        self,
        *,
        user: AuthenticatedUser,
        access_token: str,
        itinerary_id: str,
    ) -> SavedItineraryDetail | None:
        return await asyncio.to_thread(
            self._get_itinerary_sync,
            user,
            access_token,
            itinerary_id,
        )

    async def save_edit(
        self,
        *,
        user: AuthenticatedUser,
        access_token: str,
        itinerary_id: str,
        message: str,
        updated_itinerary: TripPlanData,
    ) -> SavedItineraryDetail:
        return await asyncio.to_thread(
            self._save_edit_sync,
            user,
            access_token,
            itinerary_id,
            message,
            updated_itinerary,
        )

    async def delete_itinerary(
        self,
        *,
        user: AuthenticatedUser,
        access_token: str,
        itinerary_id: str,
    ) -> bool:
        return await asyncio.to_thread(
            self._delete_itinerary_sync,
            user,
            access_token,
            itinerary_id,
        )

    async def restore_version(
        self,
        *,
        user: AuthenticatedUser,
        access_token: str,
        itinerary_id: str,
        version_number: int,
    ) -> SavedItineraryDetail:
        return await asyncio.to_thread(
            self._restore_version_sync,
            user,
            access_token,
            itinerary_id,
            version_number,
        )

    async def get_version_preview(
        self,
        *,
        user: AuthenticatedUser,
        access_token: str,
        itinerary_id: str,
        version_number: int,
    ) -> SavedItineraryVersionPreview:
        return await asyncio.to_thread(
            self._get_version_preview_sync,
            user,
            access_token,
            itinerary_id,
            version_number,
        )

    def _create_itinerary_sync(
        self,
        user: AuthenticatedUser,
        access_token: str,
        payload: SaveItineraryRequest,
    ) -> SavedItineraryDetail:
        client = self._authed_client(access_token)
        (
            client.table("user_profiles")
            .upsert(
                {
                    "id": user.id,
                    "email": user.email,
                    "updated_at": datetime.now(tz=timezone.utc).isoformat(),
                }
            )
            .execute()
        )
        title = payload.title or self._build_default_title(payload.trip_request)
        summary = payload.summary or self._build_default_summary(payload.trip_request)
        existing_itinerary = self._find_existing_itinerary_by_request_id(
            client,
            user_id=user.id,
            client_request_id=payload.client_request_id,
        )
        if existing_itinerary:
            saved_detail = self._get_itinerary_sync(
                user,
                access_token,
                existing_itinerary["id"],
            )
            if saved_detail:
                return saved_detail

        itinerary_row = {
            "user_id": user.id,
            "client_request_id": payload.client_request_id,
            "destination": payload.trip_request.destination,
            "number_of_days": payload.trip_request.number_of_days,
            "trip_start": payload.trip_request.trip_start.isoformat()
            if payload.trip_request.trip_start
            else None,
            "itinerary_type": payload.trip_request.itinerary_type,
            "budget": payload.trip_request.budget,
            "title": title,
            "summary": summary,
            "status": "saved",
            "current_version": 1,
            "source_prompt": {
                **payload.trip_request.model_dump(mode="json"),
                "client_request_id": payload.client_request_id,
            },
        }
        itinerary_response = (
            client.table("itineraries")
            .insert(itinerary_row)
            .execute()
        )
        saved_row = self._single_row(itinerary_response.data)
        itinerary_id = saved_row["id"]

        (
            client.table("itinerary_versions")
            .insert(
                {
                    "itinerary_id": itinerary_id,
                    "version_number": 1,
                    "itinerary_json": payload.current_itinerary.model_dump(mode="json"),
                }
            )
            .execute()
        )

        if payload.messages:
            (
                client.table("itinerary_messages")
                .insert(
                    [
                        {
                            "itinerary_id": itinerary_id,
                            "role": message.role,
                            "content": message.content,
                        }
                        for message in payload.messages
                    ]
                )
                .execute()
            )

        saved_detail = self._get_itinerary_sync(user, access_token, itinerary_id)
        if not saved_detail:
            raise ItineraryStoreError(
                user_message="We saved the itinerary, but couldn't load it back.",
                status_code=502,
            )
        return saved_detail

    def _list_itineraries_sync(
        self,
        user: AuthenticatedUser,
        access_token: str,
    ) -> list[SavedItinerarySummary]:
        client = self._authed_client(access_token)
        response = (
            client.table("itineraries")
            .select("*")
            .eq("user_id", user.id)
            .order("updated_at", desc=True)
            .execute()
        )
        return [
            SavedItinerarySummary.model_validate(self._normalize_summary_row(row))
            for row in response.data or []
        ]

    def _get_itinerary_sync(
        self,
        user: AuthenticatedUser,
        access_token: str,
        itinerary_id: str,
    ) -> SavedItineraryDetail | None:
        client = self._authed_client(access_token)
        itinerary_response = (
            client.table("itineraries")
            .select("*")
            .eq("user_id", user.id)
            .eq("id", itinerary_id)
            .limit(1)
            .execute()
        )
        rows = itinerary_response.data or []
        if not rows:
            return None

        itinerary_row = rows[0]
        version_response = (
            client.table("itinerary_versions")
            .select("*")
            .eq("itinerary_id", itinerary_id)
            .eq("version_number", itinerary_row["current_version"])
            .limit(1)
            .execute()
        )
        version_row = self._single_row(version_response.data)
        versions_response = (
            client.table("itinerary_versions")
            .select("version_number,created_at")
            .eq("itinerary_id", itinerary_id)
            .order("version_number", desc=True)
            .execute()
        )
        messages_response = (
            client.table("itinerary_messages")
            .select("*")
            .eq("itinerary_id", itinerary_id)
            .order("created_at")
            .execute()
        )
        return SavedItineraryDetail.model_validate(
            {
                **self._normalize_summary_row(itinerary_row),
                "trip_request": {
                    "destination": itinerary_row["destination"],
                    "number_of_days": itinerary_row["number_of_days"],
                    "trip_start": itinerary_row["trip_start"],
                    "itinerary_type": itinerary_row["itinerary_type"],
                    "budget": itinerary_row["budget"],
                },
                "current_itinerary": version_row["itinerary_json"],
                "messages": [
                    SavedItineraryMessage.model_validate(
                        {
                            "role": row["role"],
                            "content": row["content"],
                            "created_at": row["created_at"],
                        }
                    ).model_dump(mode="json")
                    for row in messages_response.data or []
                ],
                "versions": [
                    SavedItineraryVersion.model_validate(
                        {
                            "version_number": row["version_number"],
                            "created_at": row["created_at"],
                        }
                    ).model_dump(mode="json")
                    for row in versions_response.data or []
                ],
            }
        )

    def _save_edit_sync(
        self,
        user: AuthenticatedUser,
        access_token: str,
        itinerary_id: str,
        message: str,
        updated_itinerary: TripPlanData,
    ) -> SavedItineraryDetail:
        client = self._authed_client(access_token)
        current_detail = self._get_itinerary_sync(user, access_token, itinerary_id)
        if not current_detail:
            raise ItineraryStoreError(
                user_message="We couldn't find that saved itinerary.",
                status_code=404,
            )

        next_version = current_detail.current_version + 1
        now_iso = datetime.now(tz=timezone.utc).isoformat()
        (
            client.table("itinerary_versions")
            .insert(
                {
                    "itinerary_id": itinerary_id,
                    "version_number": next_version,
                    "itinerary_json": updated_itinerary.model_dump(mode="json"),
                }
            )
            .execute()
        )
        (
            client.table("itineraries")
            .update(
                {
                    "current_version": next_version,
                    "updated_at": now_iso,
                }
            )
            .eq("id", itinerary_id)
            .eq("user_id", user.id)
            .execute()
        )
        (
            client.table("itinerary_messages")
            .insert(
                [
                    {
                        "itinerary_id": itinerary_id,
                        "role": "user",
                        "content": message,
                    },
                    {
                        "itinerary_id": itinerary_id,
                        "role": "assistant",
                        "content": f"Updated the itinerary for: {message}",
                    },
                ]
            )
            .execute()
        )
        updated_detail = self._get_itinerary_sync(user, access_token, itinerary_id)
        if not updated_detail:
            raise ItineraryStoreError(
                user_message="We updated the itinerary, but couldn't load it back.",
                status_code=502,
            )
        return updated_detail

    def _delete_itinerary_sync(
        self,
        user: AuthenticatedUser,
        access_token: str,
        itinerary_id: str,
    ) -> bool:
        client = self._authed_client(access_token)
        existing_detail = self._get_itinerary_sync(user, access_token, itinerary_id)
        if not existing_detail:
            return False

        (
            client.table("itineraries")
            .delete()
            .eq("id", itinerary_id)
            .eq("user_id", user.id)
            .execute()
        )
        return True

    def _restore_version_sync(
        self,
        user: AuthenticatedUser,
        access_token: str,
        itinerary_id: str,
        version_number: int,
    ) -> SavedItineraryDetail:
        client = self._authed_client(access_token)
        current_detail = self._get_itinerary_sync(user, access_token, itinerary_id)
        if not current_detail:
            raise ItineraryStoreError(
                user_message="We couldn't find that saved itinerary.",
                status_code=404,
            )

        version_response = (
            client.table("itinerary_versions")
            .select("itinerary_json")
            .eq("itinerary_id", itinerary_id)
            .eq("version_number", version_number)
            .limit(1)
            .execute()
        )
        version_rows = version_response.data or []
        if not version_rows:
            raise ItineraryStoreError(
                user_message="We couldn't find that saved version.",
                status_code=404,
            )

        restored_itinerary = TripPlanData.model_validate(version_rows[0]["itinerary_json"])
        next_version = current_detail.current_version + 1
        now_iso = datetime.now(tz=timezone.utc).isoformat()

        (
            client.table("itinerary_versions")
            .insert(
                {
                    "itinerary_id": itinerary_id,
                    "version_number": next_version,
                    "itinerary_json": restored_itinerary.model_dump(mode="json"),
                }
            )
            .execute()
        )
        (
            client.table("itineraries")
            .update(
                {
                    "current_version": next_version,
                    "updated_at": now_iso,
                }
            )
            .eq("id", itinerary_id)
            .eq("user_id", user.id)
            .execute()
        )
        (
            client.table("itinerary_messages")
            .insert(
                [
                    {
                        "itinerary_id": itinerary_id,
                        "role": "user",
                        "content": f"Restore version {version_number}",
                    },
                    {
                        "itinerary_id": itinerary_id,
                        "role": "assistant",
                        "content": (
                            f"Restored the itinerary to version {version_number} "
                            f"and saved it as version {next_version}."
                        ),
                    },
                ]
            )
            .execute()
        )

        updated_detail = self._get_itinerary_sync(user, access_token, itinerary_id)
        if not updated_detail:
            raise ItineraryStoreError(
                user_message="We restored the itinerary, but couldn't load it back.",
                status_code=502,
            )
        return updated_detail

    def _get_version_preview_sync(
        self,
        user: AuthenticatedUser,
        access_token: str,
        itinerary_id: str,
        version_number: int,
    ) -> SavedItineraryVersionPreview:
        client = self._authed_client(access_token)
        itinerary_response = (
            client.table("itineraries")
            .select("id,user_id")
            .eq("user_id", user.id)
            .eq("id", itinerary_id)
            .limit(1)
            .execute()
        )
        if not (itinerary_response.data or []):
            raise ItineraryStoreError(
                user_message="We couldn't find that saved itinerary.",
                status_code=404,
            )

        version_response = (
            client.table("itinerary_versions")
            .select("version_number,created_at,itinerary_json")
            .eq("itinerary_id", itinerary_id)
            .eq("version_number", version_number)
            .limit(1)
            .execute()
        )
        version_rows = version_response.data or []
        if not version_rows:
            raise ItineraryStoreError(
                user_message="We couldn't find that saved version.",
                status_code=404,
            )

        version_row = version_rows[0]
        return SavedItineraryVersionPreview.model_validate(
            {
                "itinerary_id": itinerary_id,
                "version_number": version_row["version_number"],
                "created_at": version_row["created_at"],
                "itinerary": version_row["itinerary_json"],
            }
        )

    def _find_existing_itinerary_by_request_id(
        self,
        client: Client,
        *,
        user_id: str,
        client_request_id: str,
    ) -> dict | None:
        response = (
            client.table("itineraries")
            .select("id,client_request_id,created_at")
            .eq("user_id", user_id)
            .eq("client_request_id", client_request_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        return rows[0] if rows else None

    def _authed_client(self, access_token: str) -> Client:
        if not self.is_configured:
            raise ItineraryStoreError(
                user_message="Saved itineraries are not configured on the backend.",
                status_code=503,
            )

        client = create_client(
            self._supabase_url,
            self._supabase_anon_key,
            options=ClientOptions(
                auto_refresh_token=False,
                persist_session=False,
            ),
        )
        client.postgrest.auth(access_token)
        return client

    @staticmethod
    def _single_row(rows: list[dict] | None) -> dict:
        if not rows:
            raise ItineraryStoreError(
                user_message="Expected a saved itinerary row, but none was returned.",
                status_code=502,
            )
        return rows[0]

    @staticmethod
    def _build_default_title(request: TripPlanRequest) -> str:
        return f"{request.destination} {request.number_of_days}-day trip"

    @staticmethod
    def _build_default_summary(request: TripPlanRequest) -> str:
        return (
            f"{request.itinerary_type} itinerary for {request.destination} "
            f"with a {request.budget.lower()} budget."
        )

    @staticmethod
    def _normalize_summary_row(row: dict) -> dict:
        trip_start = row.get("trip_start")
        if isinstance(trip_start, str):
            trip_start = date.fromisoformat(trip_start)
        elif isinstance(trip_start, datetime):
            trip_start = trip_start.date()

        return {
            "id": row["id"],
            "destination": row["destination"],
            "number_of_days": row["number_of_days"],
            "trip_start": trip_start,
            "itinerary_type": row["itinerary_type"],
            "budget": row["budget"],
            "title": row["title"],
            "summary": row.get("summary"),
            "status": row.get("status", "saved"),
            "current_version": row["current_version"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
