import "./style.css";

const SkeletonBlock = ({ className = "", style = {} }) => {
  return <div className={`skeleton-block ${className}`.trim()} style={style} />;
};

export default SkeletonBlock;
