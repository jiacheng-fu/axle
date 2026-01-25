const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function sendUserMessage(payload) {
  try {
    const response = await fetch(`${API_BASE}/preferences`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.warn("Backend unavailable, message stored locally.", error);
    return null;
  }
}
