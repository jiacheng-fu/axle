import React, { useEffect, useRef } from "react";

export default function MessageList({ messages }) {
  const endRef = useRef(null);
  const listRef = useRef(null);

  useEffect(() => {
    // Scroll to bottom when messages change
    if (listRef.current) {
      // Use setTimeout to ensure DOM has updated
      setTimeout(() => {
        // Scroll only the message list container, not the entire page
        if (listRef.current) {
          listRef.current.scrollTop = listRef.current.scrollHeight;
        }
      }, 100);
    }
  }, [messages]);

  return (
    <div ref={listRef} className="message-list" role="log" aria-live="polite">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`message message-${message.role}`}
        >
          <div className="message-inner">
            <span className="message-role">
              {message.role === "bot" ? "Scout" : "You"}
            </span>
            <p>{message.text}</p>
          </div>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
