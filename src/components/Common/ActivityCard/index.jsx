import "./style.css";

const ActivityCard = ({ activity, activityNumber }) => {
  return (
    <div className="activity-card">
      <div className="activity-number">{activityNumber}</div>
      <div className="main-info-wrapper">
        <div className="timing">{activity?.time}</div>
        <div className="text">{activity?.name}</div>
        <div className="text">{activity?.location}</div>
        <div className="detail-text">
          <span>{activity?.price}₹</span> <span className="dot"></span>{" "}
          <span> {activity?.duration}</span>
        </div>
      </div>
      <div className="detail-text">{activity?.description}</div>
    </div>
  );
};

export default ActivityCard;
