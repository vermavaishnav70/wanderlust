import "./style.css";
import BrandHeader from "../Common/BrandHeader/index.jsx";
import Card from "../Common/Card/index.jsx";
import Button from "../Common/Button/index.jsx";
import { Link, useLocation } from "react-router-dom";
import Loading from "../Common/Loading/index.jsx";
import ErrorScreen from "../ErrorScreen/index.jsx";
import { createTripPrompt } from "../../utils/prompt.js";
import { useEffect, useState } from "react";
import {
  generateContentWithGemini,
  generateContentWithGroq,
} from "../../utils/apiService.js";

const ItineraryScreen = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const location = useLocation();
  const { inputValues } = location.state || {};
  const prompt = createTripPrompt({
    where_to: inputValues[1],
    number_of_days: inputValues[2],
    trip_start: inputValues[3],
    itinerary_type: inputValues[4],
    budget: inputValues[5],
    travel_preference: "",
  });

  // Function to fetch and set data
  const fetchData = async () => {
    setLoading(true);

    // Check if data exists in sessionStorage
    const storedData = sessionStorage.getItem("itineraryData");
    if (storedData) {
      setData(JSON.parse(storedData)); // Use stored data if available
      setLoading(false);
      return;
    }

    try {
      // Attempt to fetch data with Gemini
      console.log('calling generateContentWithGemini');
      const response = await generateContentWithGemini(prompt);
      console.log("response", response);
      setData(response);
      sessionStorage.setItem("itineraryData", JSON.stringify(response)); // Store in sessionStorage
    } catch (geminiError) {
      try {
        // Fallback to Groq if Gemini fails
        console.log('calling generateContentWithGroq');
        const backupResponse = await generateContentWithGroq(prompt);
        console.log("backupResponse", backupResponse);
        setData(backupResponse);
        sessionStorage.setItem("itineraryData", JSON.stringify(backupResponse)); // Store in sessionStorage
      } catch (rgroqError) {
        setError(
          `Failed to fetch data. ${geminiError.message || rgroqError.message}`
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []); // Empty dependency array to call fetchData only once when component mounts

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
          onClick={() => sessionStorage.removeItem("itineraryData")}
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
};

export default ItineraryScreen;
