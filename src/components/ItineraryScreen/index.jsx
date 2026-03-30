import "./style.css";
import BrandHeader from "../Common/BrandHeader/index.jsx";
import Card from "../Common/Card/index.jsx";
import Button from "../Common/Button/index.jsx";
import { Link, useLocation } from "react-router-dom";
import Loading from "../Common/Loading/index.jsx";
import ErrorScreen from "../ErrorScreen/index.jsx";
import { useEffect, useState } from "react";
import { planTrip } from "../../utils/apiService.js";

const ItineraryScreen = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const location = useLocation();
  const { inputValues } = location.state || {};

  const tripRequest = inputValues
    ? {
        destination: inputValues[1],
        number_of_days: Number(inputValues[2]),
        trip_start: inputValues[3],
        itinerary_type: inputValues[4],
        budget: inputValues[5],
      }
    : null;

  const tripRequestJson = tripRequest ? JSON.stringify(tripRequest) : null;
  const cacheKey = tripRequest
    ? `itineraryData:${tripRequestJson}`
    : null;

  useEffect(() => {
    const fetchData = async () => {
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
        setLoading(false);
        return;
      }

      try {
        const response = await planTrip(currentTripRequest);
        setData(response);
        sessionStorage.setItem(cacheKey, JSON.stringify(response));
      } catch (requestError) {
        setError(`Failed to fetch itinerary. ${requestError.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [cacheKey, tripRequestJson]); // Refetch when trip details change

  const itineraries = data?.itinerary || [];
  if (data) {
    return (
      <div className="itinerary-screen">
        <BrandHeader />
        <div className="cards-wrapper">
          {itineraries?.map((itinerary, index) => {
            return <Card itinerary={itinerary} key={index} />;
          })}
        </div>
        <Link
          to="/fill-details"
          className="back-button"
          onClick={() => {
            if (cacheKey) {
              sessionStorage.removeItem(cacheKey);
            }
          }}
        >
          <Button text="Plan a new trip" />
        </Link>
      </div>
    );
  }

  if (loading) return <Loading />;
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
