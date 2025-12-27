import { cloneElement, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Button from "../Common/Button";
import { data } from "../../utils/flightSvgData.jsx";
import "./style.css";

data.sort(() => Math.random() - 0.5);

const IntroScreen = () => {
  const [newData, setNewData] = useState({ index: 0, items: [] });
  useEffect(() => {
    const id = setInterval(() => {
      setNewData((oldData) => {
        if (oldData.index === 10) {
          clearTimeout(id);
          return oldData;
        }

        return {
          index: oldData.index + 1,
          items: [
            ...oldData.items,
            ...data.filter((_, i) => i % 10 === oldData.index),
          ],
        };
      });
    }, 50);
    return () => clearTimeout(id);
  }, []);
  return (
    <div className="introScreen">
      <div className="gradient"></div>

      {/* biome-ignore lint/a11y/noSvgWithoutTitle: <explanation> */}
      <div
        style={{ scale: "1.2", marginTop: "80px", display: "flex", flex: 1 }}
      >
        <svg
          width="344"
          height="512"
          viewBox="0 0 344 512"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          {newData.items.map((item, index) =>
            cloneElement(item, { key: `flight-dot-${index}` })
          )}
        </svg>
      </div>

      <div className="brand-wrapper">
        <div className="intro-brand-name">Wanderlust</div>
        <div className="brand-text">Plan your ultimate trip with AI</div>
      </div>
      <Link to="/fill-details" className="CTA-button">
        <Button text="Let's Start" />
      </Link>
    </div>
  );
};

export default IntroScreen;
