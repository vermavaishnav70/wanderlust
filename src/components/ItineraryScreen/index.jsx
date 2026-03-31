import "./style.css";
import BrandHeader from "../Common/BrandHeader/index.jsx";
import Card from "../Common/Card/index.jsx";
import Button from "../Common/Button/index.jsx";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";
import ErrorScreen from "../ErrorScreen/index.jsx";
import NotFoundScreen from "../NotFoundScreen/index.jsx";
import { useCallback, useEffect, useState } from "react";
import ChatPanel from "../ChatPanel/index.jsx";
import WeatherPreview from "../WeatherPreview/index.jsx";
import AuthPrompt from "../AuthPrompt/index.jsx";
import ItinerarySkeleton from "./ItinerarySkeleton.jsx";
import SkeletonBlock from "../Common/SkeletonBlock/index.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import {
  deleteSavedItinerary,
  editSavedItinerary,
  editTrip,
  fetchTripWeather,
  getSavedItinerary,
  getSavedItineraryVersion,
  planTrip,
  restoreSavedItineraryVersion,
  saveItinerary,
} from "../../utils/apiService.js";

const PENDING_SAVE_KEY = "pendingItinerarySave";
const PENDING_SAVE_LOCK_KEY = "pendingItinerarySaveInFlight";
const PANEL_WEATHER = "weather";
const PANEL_VERSIONS = "versions";
const PANEL_LOGS = "Activity";
const createClientRequestId = () =>
  globalThis.crypto?.randomUUID?.() ??
  `save-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const ItineraryScreen = () => {
  const [savedTrip, setSavedTrip] = useState(null);
  const [data, setData] = useState(null);
  const [weather, setWeather] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [restoringVersion, setRestoringVersion] = useState(null);
  const [previewingVersion, setPreviewingVersion] = useState(null);
  const [versionPreview, setVersionPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saveError, setSaveError] = useState("");
  const [showAuthPrompt, setShowAuthPrompt] = useState(false);
  const [savedTripMissing, setSavedTripMissing] = useState(false);
  const [sessionExpired, setSessionExpired] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { itineraryId } = useParams();
  const { accessToken, isConfigured, signOut, user } = useAuth();
  const { inputValues } = location.state || {};
  const isSavedMode = Boolean(itineraryId);
  const [activePanel, setActivePanel] = useState(PANEL_WEATHER);

  const draftTripRequest = inputValues
    ? {
        destination: inputValues[1],
        number_of_days: Number(inputValues[2]),
        trip_start: inputValues[3],
        itinerary_type: inputValues[4],
        budget: inputValues[5],
      }
    : null;
  const tripRequest = savedTrip?.trip_request || draftTripRequest;

  const tripRequestJson = draftTripRequest ? JSON.stringify(draftTripRequest) : null;
  const cacheKey = draftTripRequest
    ? `itineraryData:${tripRequestJson}`
    : null;
  const [saveRequestId, setSaveRequestId] = useState(() => createClientRequestId());

  const completeSave = useCallback(
    async (payload) => {
      if (sessionStorage.getItem(PENDING_SAVE_LOCK_KEY) === "true") {
        return;
      }

      sessionStorage.setItem(PENDING_SAVE_LOCK_KEY, "true");
      const response = await saveItinerary({
        accessToken,
        client_request_id: payload.client_request_id,
        ...payload,
      });
      sessionStorage.removeItem(PENDING_SAVE_KEY);
      sessionStorage.removeItem(PENDING_SAVE_LOCK_KEY);
      navigate(`/saved-trips/${response.id}`);
    },
    [accessToken, navigate]
  );

  const loadWeather = useCallback(async (request) => {
    if (!request?.trip_start) {
      setWeather(null);
      setWeatherLoading(false);
      return;
    }

    setWeatherLoading(true);
    try {
      const response = await fetchTripWeather(request);
      setWeather(response);
    } catch {
      setWeather(null);
    } finally {
      setWeatherLoading(false);
    }
  }, []);

  useEffect(() => {
    setActivePanel(PANEL_WEATHER);
  }, [isSavedMode]);

  useEffect(() => {
    const fetchDraftData = async () => {
      setLoading(true);
      setError(null);
      const currentTripRequest = tripRequestJson
        ? JSON.parse(tripRequestJson)
        : null;

      if (!currentTripRequest || !cacheKey) {
        setError(
          "Missing trip details. Please fill in your trip preferences again."
        );
        setLoading(false);
        return;
      }

      const storedData = sessionStorage.getItem(cacheKey);
      if (storedData) {
        setData(JSON.parse(storedData));
        setMessages([]);
        loadWeather(currentTripRequest);
        setLoading(false);
        return;
      }

      try {
        const response = await planTrip(currentTripRequest);
        setData(response);
        sessionStorage.setItem(cacheKey, JSON.stringify(response));
        setLoading(false);
        loadWeather(currentTripRequest);
      } catch (requestError) {
        setError(`Failed to fetch itinerary. ${requestError.message}`);
        setLoading(false);
      }
    };

    const fetchSavedTrip = async () => {
      if (!itineraryId) {
        return;
      }

      if (!accessToken) {
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      setSavedTripMissing(false);
      setSessionExpired(false);

      try {
        const response = await getSavedItinerary(accessToken, itineraryId);
        setSavedTrip(response);
        setData(response.current_itinerary);
        setMessages(response.messages || []);
        setVersionPreview(null);
        setLoading(false);
        loadWeather(response.trip_request);
      } catch (requestError) {
        const normalizedMessage = requestError.message.toLowerCase();
        if (normalizedMessage.includes("not found")) {
          setSavedTripMissing(true);
          setError(null);
        } else if (
          normalizedMessage.includes("authentication required") ||
          normalizedMessage.includes("invalid or has expired")
        ) {
          setSessionExpired(true);
          setError(null);
          await signOut();
        } else {
          setError(`Failed to load saved itinerary. ${requestError.message}`);
        }
        setLoading(false);
      }
    };

    if (isSavedMode) {
      fetchSavedTrip();
      return;
    }

    fetchDraftData();
  }, [accessToken, cacheKey, isSavedMode, itineraryId, loadWeather, signOut, tripRequestJson]);

  useEffect(() => {
    const autoSavePendingDraft = async () => {
      if (!accessToken || isSavedMode || saving) {
        return;
      }

      const pendingDraft = sessionStorage.getItem(PENDING_SAVE_KEY);
      if (!pendingDraft) {
        return;
      }

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
        setSaving(true);
        setSaveError("");
        await completeSave(normalizedDraft);
      } catch (requestError) {
        setSaveError(`Failed to auto-save itinerary. ${requestError.message}`);
        sessionStorage.removeItem(PENDING_SAVE_LOCK_KEY);
      } finally {
        setSaving(false);
      }
    };

    autoSavePendingDraft();
  }, [accessToken, completeSave, isSavedMode, saving]);

  const handleEdit = async (message) => {
    if (!tripRequest || !data) {
      return;
    }

    const nextMessages = [...messages, { role: "user", content: message }];
    setMessages(nextMessages);
    setEditing(true);
    setError(null);

    try {
      if (isSavedMode && itineraryId && accessToken) {
        const response = await editSavedItinerary({
          accessToken,
          itineraryId,
          message,
        });
        setSavedTrip(response);
        setData(response.current_itinerary);
        setMessages(response.messages || []);
      } else {
        const response = await editTrip({
          trip_request: tripRequest,
          current_itinerary: data,
          message,
        });
        setData(response);
        const finalMessages = [
          ...nextMessages,
          {
            role: "assistant",
            content: `Updated the itinerary for: ${message}`,
          },
        ];
        setMessages(finalMessages);
        if (cacheKey) {
          sessionStorage.setItem(cacheKey, JSON.stringify(response));
        }
      }
    } catch (requestError) {
      setError(`Failed to update itinerary. ${requestError.message}`);
    } finally {
      setEditing(false);
    }
  };

  const handleSave = async () => {
    if (!tripRequest || !data || saving) {
      return;
    }

    if (!isConfigured) {
      setSaveError(
        "Supabase auth is not configured yet. Add the Vite Supabase env vars first."
      );
      return;
    }

    if (!accessToken) {
      const pendingPayload = {
        trip_request: tripRequest,
        current_itinerary: data,
        client_request_id: saveRequestId,
        messages,
        title: `${tripRequest.destination} ${tripRequest.number_of_days}-day trip`,
      };
      sessionStorage.setItem(
        PENDING_SAVE_KEY,
        JSON.stringify(pendingPayload)
      );
      setShowAuthPrompt(true);
      return;
    }

    setSaving(true);
    setSaveError("");

    try {
      await completeSave({
        trip_request: tripRequest,
        current_itinerary: data,
        client_request_id: saveRequestId,
        messages,
        title: `${tripRequest.destination} ${tripRequest.number_of_days}-day trip`,
      });
      setSaveRequestId(createClientRequestId());
    } catch (requestError) {
      setSaveError(requestError.message);
      sessionStorage.removeItem(PENDING_SAVE_LOCK_KEY);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!accessToken || !itineraryId || deleting) {
      return;
    }

    setDeleting(true);
    setSaveError("");

    try {
      await deleteSavedItinerary({
        accessToken,
        itineraryId,
      });
      navigate("/saved-trips");
    } catch (requestError) {
      const normalizedMessage = requestError.message.toLowerCase();
      if (normalizedMessage.includes("not found")) {
        setSavedTripMissing(true);
        setSaveError("");
      } else if (
        normalizedMessage.includes("authentication required") ||
        normalizedMessage.includes("invalid or has expired")
      ) {
        setSessionExpired(true);
        setSaveError("");
        await signOut();
      } else {
        setSaveError(requestError.message);
      }
    } finally {
      setDeleting(false);
    }
  };

  const handleRestoreVersion = async (versionNumber) => {
    if (!accessToken || !itineraryId || restoringVersion) {
      return;
    }

    setRestoringVersion(versionNumber);
    setSaveError("");

    try {
      const response = await restoreSavedItineraryVersion({
        accessToken,
        itineraryId,
        versionNumber,
      });
      setSavedTrip(response);
      setData(response.current_itinerary);
      setMessages(response.messages || []);
      setVersionPreview(null);
    } catch (requestError) {
      const normalizedMessage = requestError.message.toLowerCase();
      if (normalizedMessage.includes("not found")) {
        setSavedTripMissing(true);
        setSaveError("");
      } else if (
        normalizedMessage.includes("authentication required") ||
        normalizedMessage.includes("invalid or has expired")
      ) {
        setSessionExpired(true);
        setSaveError("");
        await signOut();
      } else {
        setSaveError(requestError.message);
      }
    } finally {
      setRestoringVersion(null);
    }
  };

  const handlePreviewVersion = async (versionNumber) => {
    if (!accessToken || !itineraryId || previewingVersion) {
      return;
    }

    if (versionPreview?.version_number === versionNumber) {
      setVersionPreview(null);
      return;
    }

    setPreviewingVersion(versionNumber);
    setSaveError("");

    try {
      const response = await getSavedItineraryVersion({
        accessToken,
        itineraryId,
        versionNumber,
      });
      setVersionPreview(response);
    } catch (requestError) {
      const normalizedMessage = requestError.message.toLowerCase();
      if (normalizedMessage.includes("not found")) {
        setSavedTripMissing(true);
        setSaveError("");
      } else if (
        normalizedMessage.includes("authentication required") ||
        normalizedMessage.includes("invalid or has expired")
      ) {
        setSessionExpired(true);
        setSaveError("");
        await signOut();
      } else {
        setSaveError(requestError.message);
      }
    } finally {
      setPreviewingVersion(null);
    }
  };

  const itineraries = data?.itinerary || [];
  const panelTabs = [
    {
      id: PANEL_WEATHER,
      label: "Weather",
      available: Boolean(tripRequest?.trip_start) || weatherLoading,
    },
    {
      id: PANEL_VERSIONS,
      label: "Versions",
      available: isSavedMode && Boolean(savedTrip),
    },
    {
      id: PANEL_LOGS,
      label: "Activity",
      available: Boolean(messages?.length),
    },
  ].filter((tab) => tab.available);

  const renderSupportPanel = () => {
    if (activePanel === PANEL_WEATHER) {
      if (weatherLoading) {
        return (
          <div className="itinerary-history-card">
            <SkeletonBlock className="itinerary-skeleton-panel-title" />
            <SkeletonBlock className="itinerary-skeleton-panel-line" />
            <div className="itinerary-skeleton-weather-grid">
              <SkeletonBlock className="itinerary-skeleton-weather-card" />
              <SkeletonBlock className="itinerary-skeleton-weather-card" />
              <SkeletonBlock className="itinerary-skeleton-weather-card" />
            </div>
          </div>
        );
      }

      return weather?.daily?.length ? (
        <WeatherPreview weather={weather} />
      ) : (
        <div className="itinerary-history-card">
          <div className="itinerary-history-title">Weather</div>
          <div className="itinerary-history-subtitle">
            Weather context will appear here when trip dates are available.
          </div>
        </div>
      );
    }

    if (activePanel === PANEL_VERSIONS && isSavedMode && savedTrip) {
      return (
        <>
          <div className="itinerary-history-card">
            <div className="itinerary-history-title">Version history</div>
            <div className="itinerary-history-subtitle">
              Saved snapshots for this itinerary.
            </div>
            <div className="itinerary-history-list">
              {(savedTrip.versions || []).map((version) => (
                <div className="itinerary-history-item" key={version.version_number}>
                  <div className="itinerary-history-item-row">
                    <div className="itinerary-history-item-title">
                      Version {version.version_number}
                    </div>
                    <div className="itinerary-history-actions">
                      {version.version_number !== savedTrip.current_version ? (
                        <>
                          <button
                            className="itinerary-history-action"
                            disabled={previewingVersion === version.version_number}
                            onClick={() => handlePreviewVersion(version.version_number)}
                            type="button"
                          >
                            {previewingVersion === version.version_number
                              ? "Loading..."
                              : versionPreview?.version_number === version.version_number
                                ? "Hide preview"
                                : "Preview"}
                          </button>
                          <button
                            className="itinerary-history-action"
                            disabled={restoringVersion === version.version_number}
                            onClick={() => handleRestoreVersion(version.version_number)}
                            type="button"
                          >
                            {restoringVersion === version.version_number
                              ? "Restoring..."
                              : "Restore as latest"}
                          </button>
                        </>
                      ) : (
                        <span className="itinerary-history-current">Current</span>
                      )}
                    </div>
                  </div>
                  <div className="itinerary-history-item-meta">
                    {new Date(version.created_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
          {versionPreview ? (
            <div className="itinerary-preview-shell">
              <div className="itinerary-preview-header">
                <div>
                  <div className="itinerary-preview-title">
                    Previewing version {versionPreview.version_number}
                  </div>
                  <div className="itinerary-preview-subtitle">
                    This is a safe preview. Restoring will create a new latest
                    version and keep history intact.
                  </div>
                </div>
                <button
                  className="itinerary-history-action"
                  onClick={() => setVersionPreview(null)}
                  type="button"
                >
                  Close preview
                </button>
              </div>
              <div className="cards-wrapper cards-wrapper-preview">
                {(versionPreview.itinerary?.itinerary || []).map((itinerary, index) => {
                  return (
                    <Card
                      itinerary={itinerary}
                      key={`${versionPreview.version_number}-${index}`}
                    />
                  );
                })}
              </div>
            </div>
          ) : null}
        </>
      );
    }

    return (
      <div className="itinerary-history-card">
        <div className="itinerary-history-title">Edit history</div>
        <div className="itinerary-history-subtitle">
          Recent chat messages tied to this trip.
        </div>
        <div className="itinerary-history-list">
          {(messages || []).slice(-6).reverse().map((message, index) => (
            <div
              className="itinerary-history-item"
              key={`${message.role}-${message.created_at || index}`}
            >
              <div className="itinerary-history-item-title">
                {message.role === "assistant" ? "Assistant" : "You"}
              </div>
              <div className="itinerary-history-item-copy">{message.content}</div>
              {message.created_at ? (
                <div className="itinerary-history-item-meta">
                  {new Date(message.created_at).toLocaleString()}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (data) {
    return (
      <div className="itinerary-screen">
        <BrandHeader />
        <div className="itinerary-toolbar">
          <div className="itinerary-toolbar-copy">
            {isSavedMode ? (
              <>
                <div className="itinerary-toolbar-title">
                  {savedTrip?.title || "Saved itinerary"}
                </div>
                <div className="itinerary-toolbar-subtitle">
                  {savedTrip
                    ? `Version ${savedTrip.current_version} · ${savedTrip.destination}`
                    : "Loading saved trip"}
                </div>
              </>
            ) : (
              <>
                <div className="itinerary-toolbar-title">
                  {tripRequest?.destination || "Your itinerary"}
                </div>
                <div className="itinerary-toolbar-subtitle">
                  Save this draft to revisit and keep editing it later.
                </div>
              </>
            )}
          </div>
          <div className="itinerary-toolbar-actions">
            {!isSavedMode ? (
              <button
                className="itinerary-action-button primary"
                disabled={saving}
                onClick={handleSave}
                type="button"
              >
                {saving ? "Saving..." : user ? "Save trip" : "Save with sign in"}
              </button>
            ) : (
              <button
                className="itinerary-action-button danger"
                disabled={deleting}
                onClick={handleDelete}
                type="button"
              >
                {deleting ? "Deleting..." : "Delete trip"}
              </button>
            )}
            <Link className="itinerary-action-button secondary" to="/saved-trips">
              Saved trips
            </Link>
          </div>
          {saveError ? <div className="itinerary-inline-error">{saveError}</div> : null}
        </div>
        {showAuthPrompt && !user ? (
          <AuthPrompt
            title="Save this trip to your account"
            description="Sign in with a magic link and we’ll save this itinerary automatically as soon as your session is ready."
          />
        ) : null}
        {panelTabs.length ? (
          <div className="itinerary-support-shell">
            {panelTabs.length > 1 ? (
              <div className="itinerary-support-tabs">
                {panelTabs.map((tab) => (
                  <button
                    className={`itinerary-support-tab ${
                      activePanel === tab.id ? "active" : ""
                    } ${tab.id === PANEL_WEATHER && weatherLoading ? "loading" : ""}`}
                    key={tab.id}
                    onClick={() => setActivePanel(tab.id)}
                    type="button"
                  >
                    {activePanel === tab.id || (tab.id === PANEL_WEATHER && weatherLoading) ? (
                      <span
                        className={`itinerary-support-tab-active-dot ${
                          tab.id === PANEL_WEATHER && weatherLoading
                            ? "loading"
                            : ""
                        }`}
                      />
                    ) : null}
                    {tab.label}
                  </button>
                ))}
              </div>
            ) : null}
            <div className="itinerary-support-panel">{renderSupportPanel()}</div>
          </div>
        ) : null}
        <div className="cards-wrapper">
          {itineraries?.map((itinerary, index) => {
            return <Card itinerary={itinerary} key={index} />;
          })}
        </div>
        <ChatPanel messages={messages} onSend={handleEdit} sending={editing} />
        <Link
          to="/fill-details"
          className="back-button"
          onClick={() => {
            if (cacheKey && !isSavedMode) {
              sessionStorage.removeItem(cacheKey);
            }
          }}
        >
          <Button className="back-button" text="Plan a new trip" />
        </Link>
      </div>
    );
  }

  if (loading) return <ItinerarySkeleton />;
  if (savedTripMissing) return <NotFoundScreen />;
  if (sessionExpired) {
    return (
      <div className="itinerary-screen">
        <BrandHeader />
        <AuthPrompt
          title="Session expired"
          description="Sign in again to continue working with your saved itineraries."
        />
      </div>
    );
  }
  if (isSavedMode && !accessToken && !loading) {
    return (
      <div className="itinerary-screen">
        <BrandHeader />
        <AuthPrompt
          title="Sign in to open this itinerary"
          description="Saved trips belong to your account, so you’ll need to sign in before we can load this one."
        />
      </div>
    );
  }
  if (error && !loading) {
    return (
      <div>
        <ErrorScreen errorMessage={error} />
      </div>
    );
  }

  return null;
};

export default ItineraryScreen;
