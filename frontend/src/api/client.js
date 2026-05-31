const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// Dealers within `radius` miles of `zip` for the map-based location picker.
// Returns { valid, error?, zip, radius, origin:{lat,lng}, dealers:[...] } or null on network error.
export async function fetchDealers(zip, radius) {
  try {
    const params = new URLSearchParams({ zip: String(zip), radius: String(radius) });
    const response = await fetch(`${API_BASE}/dealers?${params.toString()}`);
    if (!response.ok) throw new Error(`Backend responded with ${response.status}`);
    return await response.json();
  } catch (error) {
    console.warn("fetchDealers failed.", error);
    return null;
  }
}

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
