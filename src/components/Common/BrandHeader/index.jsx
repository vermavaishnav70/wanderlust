import { Link } from "react-router-dom";

import BrandLogo from "../../../assets/brand-logo.svg";
import { useAuth } from "../../../context/AuthContext.jsx";
import "./style.css";

const getAvatarLabel = (user) => {
  const email = user?.email?.trim();
  if (email) {
    return email[0].toUpperCase();
  }

  return "U";
};

const BrandHeader = ({ showSavedTripsShortcut = false }) => {
  const { user } = useAuth();
  const shouldShowShortcut = showSavedTripsShortcut && Boolean(user);

  return (
    <div className="brand-header">
      <div className="brand-header-inner">
        <img src={BrandLogo} alt="Brand Logo" />
        <div className="brand-name-wrapper">
          <h1 className="brand-name">Wanderlust</h1>
        </div>
      </div>
      {shouldShowShortcut ? (
        <Link
          aria-label="Open saved trips"
          className="brand-avatar-link"
          to="/saved-trips"
          title="Saved trips"
        >
          {getAvatarLabel(user)}
        </Link>
      ) : null}
    </div>
  );
};

export default BrandHeader;
