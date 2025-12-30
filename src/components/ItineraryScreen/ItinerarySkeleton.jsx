import BrandHeader from "../Common/BrandHeader/index.jsx";
import SkeletonBlock from "../Common/SkeletonBlock/index.jsx";
import "./style.css";

const ItinerarySkeleton = () => {
  return (
    <div className="itinerary-screen">
      <BrandHeader />
      <div className="itinerary-toolbar">
        <div className="itinerary-toolbar-copy">
          <SkeletonBlock className="itinerary-skeleton-title" />
          <SkeletonBlock className="itinerary-skeleton-subtitle" />
        </div>
        <div className="itinerary-toolbar-actions">
          <SkeletonBlock className="itinerary-skeleton-button" />
          <SkeletonBlock className="itinerary-skeleton-button" />
        </div>
      </div>

      <div className="itinerary-support-shell">
        <div className="itinerary-support-tabs">
          <SkeletonBlock className="itinerary-skeleton-pill" />
          <SkeletonBlock className="itinerary-skeleton-pill" />
          <SkeletonBlock className="itinerary-skeleton-pill" />
        </div>
        <div className="itinerary-support-panel">
          <div className="itinerary-history-card">
            <SkeletonBlock className="itinerary-skeleton-panel-title" />
            <SkeletonBlock className="itinerary-skeleton-panel-line" />
            <div className="itinerary-skeleton-weather-grid">
              <SkeletonBlock className="itinerary-skeleton-weather-card" />
              <SkeletonBlock className="itinerary-skeleton-weather-card" />
              <SkeletonBlock className="itinerary-skeleton-weather-card" />
            </div>
          </div>
        </div>
      </div>

      <div className="cards-wrapper">
        <div className="itinerary-skeleton-card">
          <SkeletonBlock className="itinerary-skeleton-card-image" />
          <div className="itinerary-skeleton-card-content">
            <SkeletonBlock className="itinerary-skeleton-card-title" />
            <SkeletonBlock className="itinerary-skeleton-card-activity" />
            <SkeletonBlock className="itinerary-skeleton-card-activity" />
            <SkeletonBlock className="itinerary-skeleton-card-activity short" />
          </div>
        </div>
        <div className="itinerary-skeleton-card">
          <SkeletonBlock className="itinerary-skeleton-card-image" />
          <div className="itinerary-skeleton-card-content">
            <SkeletonBlock className="itinerary-skeleton-card-title" />
            <SkeletonBlock className="itinerary-skeleton-card-activity" />
            <SkeletonBlock className="itinerary-skeleton-card-activity short" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ItinerarySkeleton;
