import { useState } from "react";

import "./style.css";

const ChatPanel = ({ messages, onSend, sending }) => {
  const [value, setValue] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    const nextValue = value.trim();
    if (!nextValue || sending) {
      return;
    }

    setValue("");
    await onSend(nextValue);
  };

  return (
    <div className="chat-panel">
      <div className="chat-panel-header">
        <div className="chat-panel-title">Refine your itinerary</div>
        <div className="chat-panel-copy">
          Ask for changes like “make day 2 more indoor” or “add a food market at night.”
        </div>
      </div>
      <div className="chat-message-list">
        {messages.length === 0 ? (
          <div className="chat-empty-state">
            No edits yet. Send a request and the planner will return a revised itinerary.
          </div>
        ) : (
          messages.map((message, index) => (
            <div className={`chat-bubble ${message.role}`} key={`${message.role}-${index}`}>
              <div className="chat-role">
                {message.role === "user" ? "You" : "Planner"}
              </div>
              <div className="chat-content">{message.content}</div>
            </div>
          ))
        )}
      </div>
      <form className="chat-form" onSubmit={handleSubmit}>
        <textarea
          className="chat-input"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder="Tell the planner what to change"
        />
        <button className="chat-submit" disabled={sending} type="submit">
          {sending ? "Updating..." : "Update trip"}
        </button>
      </form>
    </div>
  );
};

export default ChatPanel;
