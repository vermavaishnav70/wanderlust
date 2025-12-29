import { useState } from "react";

import { useAuth } from "../../context/AuthContext.jsx";
import "./style.css";

const AuthPrompt = ({ title, description, onSignedIn }) => {
  const { isConfigured, signInWithGoogle, signInWithOtp } = useAuth();
  const [email, setEmail] = useState("");
  const [sending, setSending] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!email.trim() || sending) {
      return;
    }

    setSending(true);
    setError("");
    setMessage("");

    try {
      await signInWithOtp(email.trim());
      setMessage("Magic link sent. Open it on this device, then come back here.");
      if (onSignedIn) {
        onSignedIn();
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSending(false);
    }
  };

  const handleGoogleSignIn = async () => {
    if (oauthLoading) {
      return;
    }

    setOauthLoading(true);
    setError("");
    setMessage("");

    try {
      await signInWithGoogle();
      if (onSignedIn) {
        onSignedIn();
      }
    } catch (requestError) {
      setError(requestError.message);
      setOauthLoading(false);
    }
  };

  if (!isConfigured) {
    return (
      <div className="auth-prompt">
        <div className="auth-prompt-title">{title}</div>
        <div className="auth-prompt-copy">
          Supabase auth is not configured yet. Add `VITE_SUPABASE_URL` and
          `VITE_SUPABASE_ANON_KEY` to enable sign-in.
        </div>
      </div>
    );
  }

  return (
    <div className="auth-prompt">
      <div className="auth-prompt-title">{title}</div>
      <div className="auth-prompt-copy">{description}</div>
      <button
        className="auth-prompt-google-button"
        disabled={oauthLoading}
        onClick={handleGoogleSignIn}
        type="button"
      >
        {oauthLoading ? "Redirecting to Google..." : "Continue with Google"}
      </button>
      <div className="auth-prompt-divider">or use magic link</div>
      <form className="auth-prompt-form" onSubmit={handleSubmit}>
        <input
          className="auth-prompt-input"
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <button className="auth-prompt-button" disabled={sending} type="submit">
          {sending ? "Sending..." : "Email me a magic link"}
        </button>
      </form>
      {message ? <div className="auth-prompt-success">{message}</div> : null}
      {error ? <div className="auth-prompt-error">{error}</div> : null}
    </div>
  );
};

export default AuthPrompt;
