const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
console.log(import.meta.env.VITE_API_BASE_URL);

const normalizeApiError = async (response) => {
  try {
    const payload = await response.json();
    return payload.error || payload.detail || `Request failed: ${response.status}`;
  } catch (error) {
    return `Request failed: ${response.status}`;
  }
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
