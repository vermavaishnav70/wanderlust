import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import BrandHeader from "../Common/BrandHeader/index.jsx";
import AuthPrompt from "../AuthPrompt/index.jsx";
import SavedTripsSkeleton from "./SavedTripsSkeleton.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import {
  deleteSavedItinerary,
  listSavedItineraries,
  saveItinerary,
} from "../../utils/apiService.js";
import "./style.css";

const PENDING_SAVE_KEY = "pendingItinerarySave";
const PENDING_SAVE_LOCK_KEY = "pendingItinerarySaveInFlight";
const createClientRequestId = () =>
  globalThis.crypto?.randomUUID?.() ??
  `save-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const SavedTripsScreen = () => {
  const { accessToken, loading: authLoading, signOut, user } = useAuth();
  const navigate = useNavigate();
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [deletingTripId, setDeletingTripId] = useState("");
  const [autoSaving, setAutoSaving] = useState(false);

  useEffect(() => {
    const autoSavePendingDraft = async () => {
      if (!accessToken) {
        return;
      }

      const pendingDraft = sessionStorage.getItem(PENDING_SAVE_KEY);
      if (!pendingDraft) {
        return;
      }

      if (sessionStorage.getItem(PENDING_SAVE_LOCK_KEY) === "true") {
        return;
      }

      setAutoSaving(true);
      setError("");
      sessionStorage.setItem(PENDING_SAVE_LOCK_KEY, "true");

      try {
        const parsedDraft = JSON.parse(pendingDraft);
        const normalizedDraft = parsedDraft.client_request_id
          ? parsedDraft
          : {
              ...parsedDraft,
              client_request_id: createClientRequestId(),
            };
        if (!parsedDraft.client_request_id) {
          sessionStorage.setItem(PENDING_SAVE_KEY, JSON.stringify(normalizedDraft));
        }
        const response = await saveItinerary({
          accessToken,
          ...normalizedDraft,
        });
        sessionStorage.removeItem(PENDING_SAVE_KEY);
        sessionStorage.removeItem(PENDING_SAVE_LOCK_KEY);
        navigate(`/saved-trips/${response.id}`, { replace: true });
      } catch (requestError) {
        setError(`Failed to auto-save itinerary. ${requestError.message}`);
        sessionStorage.removeItem(PENDING_SAVE_LOCK_KEY);
      } finally {
        setAutoSaving(false);
      }
    };

    autoSavePendingDraft();
  }, [accessToken, navigate]);

  useEffect(() => {
    const fetchTrips = async () => {
      if (!accessToken) {
        setTrips([]);
        return;
      }

      if (sessionStorage.getItem(PENDING_SAVE_KEY)) {
        return;
      }

      setLoading(true);
      setError("");
      try {
        const response = await listSavedItineraries(accessToken);
        setTrips(response || []);
      } catch (requestError) {
        setError(requestError.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTrips();
  }, [accessToken]);

  const handleDelete = async (event, itineraryId) => {
    event.preventDefault();
    event.stopPropagation();
    if (!accessToken || deletingTripId) {
      return;
    }

    setDeletingTripId(itineraryId);
    setError("");
    try {
      await deleteSavedItinerary({
        accessToken,
        itineraryId,
      });
      setTrips((currentTrips) =>
        currentTrips.filter((trip) => trip.id !== itineraryId)
      );
      navigate("/saved-trips");
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setDeletingTripId("");
    }
  };

  if (user && (authLoading || loading || autoSaving)) {
    return <SavedTripsSkeleton />;
  }

  return (
    <div className="saved-trips-screen">
      <BrandHeader />
      {!user ? (
        <AuthPrompt
          title="Sign in to see your saved trips"
          description="We’ll keep your itineraries tied to your account so you can revisit and keep editing them."
        />
      ) : (
        <>
          <div className="saved-trips-toolbar">
            <div>
              <div className="saved-trips-label">Signed in as</div>
              <div className="saved-trips-email">{user.email}</div>
            </div>
            <button className="saved-trips-ghost" onClick={() => signOut()} type="button">
              Sign out
            </button>
          </div>
          <div className="saved-trips-heading">
            <div className="saved-trips-title">Saved itineraries</div>
            <div className="saved-trips-subtitle">
              Open any trip to continue editing it in chat.
            </div>
          </div>
          {error ? <div className="saved-trips-error">{error}</div> : null}
          {!loading && !authLoading && !autoSaving && !error && trips.length === 0 ? (
            <div className="saved-trips-empty">
              No saved trips yet. Save one from the itinerary screen.
            </div>
          ) : null}
          <div className="saved-trips-list">
            {trips.map((trip) => (
              <div className="saved-trip-card-shell" key={trip.id}>
                <Link className="saved-trip-card" to={`/saved-trips/${trip.id}`}>
                  <div className="saved-trip-card-top">
                    <div>
                      <div className="saved-trip-card-title">{trip.title}</div>
                      <div className="saved-trip-card-summary">
                        {trip.summary || `${trip.destination} getaway`}
                      </div>
                    </div>
                    <div className="saved-trip-card-version">v{trip.current_version}</div>
                  </div>
                  <div className="saved-trip-card-meta">
                    {trip.destination} · {trip.number_of_days} days · {trip.budget}
                  </div>
                </Link>
                <button
                  className="saved-trip-card-delete"
                  disabled={deletingTripId === trip.id}
                  onClick={(event) => handleDelete(event, trip.id)}
                  type="button"
                >
                  {deletingTripId === trip.id ? "Deleting..." : "Delete"}
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default SavedTripsScreen;
