import BrandHeader from "../Common/BrandHeader/index.jsx";
import SkeletonBlock from "../Common/SkeletonBlock/index.jsx";
import "./style.css";

const SavedTripsSkeleton = () => {
  return (
    <div className="saved-trips-screen">
      <BrandHeader />
      <div className="saved-trips-toolbar">
        <div>
          <SkeletonBlock className="saved-trips-skeleton-label" />
          <SkeletonBlock className="saved-trips-skeleton-email" />
        </div>
        <SkeletonBlock className="saved-trips-skeleton-button" />
      </div>

      <div className="saved-trips-heading">
        <SkeletonBlock className="saved-trips-skeleton-title" />
        <SkeletonBlock className="saved-trips-skeleton-subtitle" />
      </div>

      <div className="saved-trips-list">
        <div className="saved-trip-card-shell">
          <div className="saved-trip-card">
            <div className="saved-trip-card-top">
              <div className="saved-trips-skeleton-copy">
                <SkeletonBlock className="saved-trips-skeleton-card-title" />
                <SkeletonBlock className="saved-trips-skeleton-card-summary" />
              </div>
              <SkeletonBlock className="saved-trips-skeleton-version" />
            </div>
            <SkeletonBlock className="saved-trips-skeleton-meta" />
          </div>
          <div className="saved-trip-card-delete saved-trips-skeleton-delete" />
        </div>
        <div className="saved-trip-card-shell">
          <div className="saved-trip-card">
            <div className="saved-trip-card-top">
              <div className="saved-trips-skeleton-copy">
                <SkeletonBlock className="saved-trips-skeleton-card-title" />
                <SkeletonBlock className="saved-trips-skeleton-card-summary" />
              </div>
              <SkeletonBlock className="saved-trips-skeleton-version" />
            </div>
            <SkeletonBlock className="saved-trips-skeleton-meta" />
          </div>
          <div className="saved-trip-card-delete saved-trips-skeleton-delete" />
        </div>
      </div>
    </div>
  );
};

export default SavedTripsSkeleton;
