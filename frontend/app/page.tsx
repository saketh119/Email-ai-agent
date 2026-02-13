"use client";

import { useState } from "react";

export default function Home() {
  const [emailText, setEmailText] = useState("");
  const [category, setCategory] = useState("");
  const [reply, setReply] = useState("");
  const [tokens, setTokens] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!emailText) return;

    setLoading(true);
    setError("");
    setCategory("");
    setReply("");
    setTokens(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/process-email", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email_text: emailText,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Something went wrong");
      }

      setCategory(data.category);
      setReply(data.reply);
      setTokens(data.tokens_used);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: "40px", fontFamily: "Arial" }}>
      <h1>Email AI Assistant</h1>

      <textarea
        placeholder="Paste email content here..."
        value={emailText}
        onChange={(e) => setEmailText(e.target.value)}
        rows={6}
        style={{
          width: "100%",
          padding: "10px",
          marginTop: "10px",
          fontSize: "16px",
        }}
      />

      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{
          marginTop: "15px",
          padding: "10px 20px",
          fontSize: "16px",
          cursor: "pointer",
        }}
      >
        {loading ? "Processing..." : "Generate Reply"}
      </button>

      {error && (
        <p style={{ color: "red", marginTop: "20px" }}>{error}</p>
      )}

      {category && (
        <div style={{ marginTop: "30px" }}>
          <h3>Category</h3>
          <p>{category}</p>

          <h3>Reply</h3>
          <p>{reply}</p>

          <h4>Tokens Used: {tokens}</h4>
        </div>
      )}
    </main>
  );
}
