import { useLocation } from "react-router-dom";
import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Home } from "lucide-react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
      <h1 className="font-display text-7xl font-bold text-gradient-gold mb-4">404</h1>
      <p className="text-xl text-muted-foreground mb-8 font-sans">
        Oops! Page not found
      </p>
      <Link
        to="/"
        className="hero-button-primary inline-flex items-center gap-2"
      >
        <Home className="w-5 h-5" />
        Return to Home
      </Link>
    </div>
  );
};

export default NotFound;
