import { isRouteErrorResponse, useRouteError } from "react-router-dom";

import ErrorScreen from "../ErrorScreen/index.jsx";

const getErrorMessage = (error) => {
  if (isRouteErrorResponse(error)) {
    return error.statusText || error.data || "We hit a routing error.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === "string") {
    return error;
  }

  return "We hit an unexpected error while loading this screen.";
};

const RouteErrorBoundary = () => {
  const error = useRouteError();

  return <ErrorScreen errorMessage={getErrorMessage(error)} />;
};

export default RouteErrorBoundary;
