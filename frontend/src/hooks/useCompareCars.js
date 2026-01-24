export async function compareCars(vins) {
  const res = await fetch("http://localhost:8000/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(vins)
  });
  return res.json();
}
