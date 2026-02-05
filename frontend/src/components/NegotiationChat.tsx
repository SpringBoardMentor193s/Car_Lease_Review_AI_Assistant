import { useState, useEffect, useRef } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export default function NegotiationChat() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content:
        "👋 Hi! I’m your **Car Lease Negotiation Assistant**.\n\n" +
        "I help you understand car lease agreements and negotiate better terms.\n\n" +
        "You can ask about:\n" +
        "• Monthly lease payments\n" +
        "• APR / money factor\n" +
        "• Mileage limits\n" +
        "• Down payment reduction\n" +
        "• Hidden charges & penalties\n\n" +
        "Paste your lease details or ask a question to begin.",
    },
  ]);

  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    setTimeout(() => {
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "🔍 **Lease Analysis & Negotiation Guidance**\n\n" +
          "📉 **Negotiable Areas**\n" +
          "• Monthly payment can often be reduced\n" +
          "• APR / money factor is usually negotiable\n" +
          "• Mileage allowance can be increased\n" +
          "• High down payment is not mandatory\n\n" +
          "📝 **What to Say to the Dealer**\n" +
          "“I’ve reviewed similar lease offers. If we adjust the money factor and mileage allowance, I’m ready to proceed today.”\n\n" +
          "⚠️ **Dealer Tactics to Watch**\n" +
          "• Focusing only on monthly payment\n" +
          "• Adding unnecessary accessories\n" +
          "• Claiming APR is fixed\n\n" +
          "💰 **Potential Savings**\n" +
          "Lower APR and fees can save thousands over the lease term.\n\n" +
          "Tell me your **lease duration, monthly payment, APR, and mileage limit** for more precise advice.",
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setIsTyping(false);
    }, 800);
  };

  return (
    <div
      style={{
        maxWidth: 750,
        margin: "40px auto",
        border: "1px solid #ccc",
        borderRadius: 12,
        padding: 16,
        fontFamily: "Arial, sans-serif",
      }}
    >
      <h2 style={{ textAlign: "center" }}>
        Car Lease Negotiation Assistant
      </h2>
      <p style={{ textAlign: "center", color: "#555" }}>
        Analyze leases • Negotiate smarter • Save money
      </p>

      <div
        style={{
          height: 420,
          overflowY: "auto",
          border: "1px solid #ddd",
          padding: 12,
          borderRadius: 8,
          marginBottom: 10,
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              textAlign: msg.role === "user" ? "right" : "left",
              marginBottom: 10,
            }}
          >
            <span
              style={{
                display: "inline-block",
                padding: "10px 14px",
                borderRadius: 10,
                maxWidth: "85%",
                backgroundColor:
                  msg.role === "user" ? "#4f46e5" : "#e5e7eb",
                color: msg.role === "user" ? "#fff" : "#000",
                whiteSpace: "pre-line",
              }}
            >
              {msg.content}
            </span>
          </div>
        ))}

        {isTyping && <p>Assistant is typing...</p>}
        <div ref={messagesEndRef} />
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Enter your car lease details..."
          style={{
            flex: 1,
            padding: 10,
            borderRadius: 6,
            border: "1px solid #ccc",
          }}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button
          onClick={handleSend}
          style={{
            padding: "10px 18px",
            borderRadius: 6,
            border: "none",
            backgroundColor: "#4f46e5",
            color: "white",
            cursor: "pointer",
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}
