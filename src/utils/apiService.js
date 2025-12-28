const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const normalizeApiError = async (response) => {
  try {
    const payload = await response.json();
    return payload.error || payload.detail || `Request failed: ${response.status}`;
  } catch (error) {
    return `Request failed: ${response.status}`;
  }
};

const getAuthHeaders = (accessToken) => {
  if (!accessToken) {
    return {};
  }

  return {
    Authorization: `Bearer ${accessToken}`,
  };
};

export const planTrip = async ({
  destination,
  number_of_days,
  trip_start,
  itinerary_type,
  budget,
}) => {
  const response = await fetch(`${API_BASE_URL}/api/trips/plan`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      destination,
      number_of_days,
      trip_start: trip_start || null,
      itinerary_type,
      budget,
    }),
  });

  if (!response.ok) {
    throw new Error(await normalizeApiError(response));
  }

  const payload = await response.json();
  return payload.data;
};

export const fetchTripWeather = async ({
  destination,
  number_of_days,
  trip_start,
}) => {
  if (!trip_start) {
    return null;
  }

  const query = new URLSearchParams({
    destination,
    number_of_days: `${number_of_days}`,
    trip_start,
  });
  const response = await fetch(`${API_BASE_URL}/api/trips/weather?${query.toString()}`);

  if (!response.ok) {
    throw new Error(await normalizeApiError(response));
  }

  const payload = await response.json();
  return payload.data;
};

export const editTrip = async ({
  trip_request,
  current_itinerary,
  message,
}) => {
  const response = await fetch(`${API_BASE_URL}/api/trips/edit`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      trip_request,
      current_itinerary,
      message,
    }),
  });

  if (!response.ok) {
    throw new Error(await normalizeApiError(response));
  }

  const payload = await response.json();
  return payload.data;
};

export const saveItinerary = async ({
  accessToken,
  trip_request,
  current_itinerary,
  client_request_id,
  messages,
  title,
  summary,
}) => {
  const response = await fetch(`${API_BASE_URL}/api/itineraries`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(accessToken),
    },
    body: JSON.stringify({
      trip_request,
      current_itinerary,
      client_request_id,
      messages,
      title: title || null,
      summary: summary || null,
    }),
  });

  if (!response.ok) {
    throw new Error(await normalizeApiError(response));
  }

  const payload = await response.json();
  return payload.data;
};

export const listSavedItineraries = async (accessToken) => {
  const response = await fetch(`${API_BASE_URL}/api/itineraries`, {
    headers: {
      ...getAuthHeaders(accessToken),
    },
  });

  if (!response.ok) {
    throw new Error(await normalizeApiError(response));
  }

  const payload = await response.json();
  return payload.data;
};

export const getSavedItinerary = async (accessToken, itineraryId) => {
  const response = await fetch(`${API_BASE_URL}/api/itineraries/${itineraryId}`, {
    headers: {
      ...getAuthHeaders(accessToken),
    },
  });

  if (!response.ok) {
    throw new Error(await normalizeApiError(response));
  }

  const payload = await response.json();
  return payload.data;
};

export const editSavedItinerary = async ({
  accessToken,
  itineraryId,
  message,
}) => {
  const response = await fetch(
    `${API_BASE_URL}/api/itineraries/${itineraryId}/edit`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(accessToken),
      },
      body: JSON.stringify({
        message,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(await normalizeApiError(response));
  }

  const payload = await response.json();
  return payload.data;
};

export const deleteSavedItinerary = async ({
  accessToken,
  itineraryId,
}) => {
  const response = await fetch(`${API_BASE_URL}/api/itineraries/${itineraryId}`, {
    method: "DELETE",
    headers: {
      ...getAuthHeaders(accessToken),
    },
  });

  if (!response.ok) {
    throw new Error(await normalizeApiError(response));
  }

  const payload = await response.json();
  return payload.data;
};

export const restoreSavedItineraryVersion = async ({
  accessToken,
  itineraryId,
  versionNumber,
}) => {
  const response = await fetch(
    `${API_BASE_URL}/api/itineraries/${itineraryId}/versions/${versionNumber}/restore`,
    {
      method: "POST",
      headers: {
        ...getAuthHeaders(accessToken),
      },
    }
  );

  if (!response.ok) {
    throw new Error(await normalizeApiError(response));
  }

  const payload = await response.json();
  return payload.data;
};

export const getSavedItineraryVersion = async ({
  accessToken,
  itineraryId,
  versionNumber,
}) => {
  const response = await fetch(
    `${API_BASE_URL}/api/itineraries/${itineraryId}/versions/${versionNumber}`,
    {
      headers: {
        ...getAuthHeaders(accessToken),
      },
    }
  );

  if (!response.ok) {
    throw new Error(await normalizeApiError(response));
  }

  const payload = await response.json();
  return payload.data;
};
