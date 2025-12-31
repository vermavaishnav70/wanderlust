import "./style.css";

const WeatherPreview = ({ weather }) => {
  if (!weather?.daily?.length) {
    return null;
  }

  return (
    <div className="weather-panel">
      <div className="weather-panel-title">Weather</div>
      <div className="weather-panel-location">{weather.location}</div>
      <div className="weather-day-list">
        {weather.daily.slice(0, 4).map((day) => (
          <div className="weather-day-card" key={day.date}>
            <div className="weather-date">{day.date}</div>
            <div className="weather-summary">{day.summary}</div>
            <div className="weather-temp">
              {Math.round(day.temperature_max_c)}C / {Math.round(day.temperature_min_c)}C
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WeatherPreview;
