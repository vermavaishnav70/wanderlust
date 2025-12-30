import { Link } from "react-router-dom";

import BrandHeader from "../Common/BrandHeader/index.jsx";
import Button from "../Common/Button/index.jsx";
import error from "../../assets/error.svg";
import "./style.css";

const NotFoundScreen = () => {
  return (
    <div className="not-found-screen">
      <BrandHeader />
      <div className="not-found-overlay">
        <div className="not-found-content">
          <img className="not-found-image" src={error} alt="Page not found" />
          <div className="not-found-copy">
            <div className="not-found-title">Page not found</div>
            <div className="not-found-description">
              The page you are looking for does not exist or may have moved.
            </div>
          </div>
          <div className="not-found-actions">
            <Link className="not-found-link" to="/">
              <Button text="Back to home" />
            </Link>
            <Link className="not-found-link" to="/fill-details">
              <Button text="Plan a trip" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotFoundScreen;
