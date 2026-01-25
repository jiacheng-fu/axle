import React, { useEffect, useRef } from "react";

export default function MessageList({ messages }) {
  const endRef = useRef(null);
  const listRef = useRef(null);

  useEffect(() => {
    const list = listRef.current;
    if (!list) return;
    requestAnimationFrame(() => {
      list.scrollTo({ top: list.scrollHeight, behavior: "smooth" });
    });
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
