import "./App.css";
import "./fonts/GeistVariableVF.ttf";
import { Suspense, lazy } from "react";
import { RouterProvider, createBrowserRouter } from "react-router-dom";
import Loading from "./components/Common/Loading/index.jsx";
import RouteErrorBoundary from "./components/RouteErrorBoundary/index.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";

const IntroScreen = lazy(() => import("./components/IntroScreen"));
const MainScreen = lazy(() => import("./components/MainScreen"));
const ItineraryScreen = lazy(() => import("./components/ItineraryScreen"));
const SavedTripsScreen = lazy(() => import("./components/SavedTripsScreen/index.jsx"));
const NotFoundScreen = lazy(() => import("./components/NotFoundScreen/index.jsx"));

const withSuspense = (element) => (
  <Suspense fallback={<Loading />}>{element}</Suspense>
);

function App() {
  const router = createBrowserRouter([
    {
      path: "/",
      element: withSuspense(<IntroScreen />),
      errorElement: <RouteErrorBoundary />,
    },
    {
      path: "/fill-details",
      element: withSuspense(<MainScreen />),
      errorElement: <RouteErrorBoundary />,
    },
    {
      path: "/your-itinerary",
      element: withSuspense(<ItineraryScreen />),
      errorElement: <RouteErrorBoundary />,
    },
    {
      path: "/saved-trips",
      element: withSuspense(<SavedTripsScreen />),
      errorElement: <RouteErrorBoundary />,
    },
    {
      path: "/saved-trips/:itineraryId",
      element: withSuspense(<ItineraryScreen />),
      errorElement: <RouteErrorBoundary />,
    },
    {
      path: "*",
      element: withSuspense(<NotFoundScreen />),
      errorElement: <RouteErrorBoundary />,
    },
  ]);

  return (
    <AuthProvider>
      <RouterProvider router={router} />
    </AuthProvider>
  );
}

export default App;
