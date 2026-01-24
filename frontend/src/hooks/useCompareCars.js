export async function compareCars(vins) {
  const res = await fetch("http://localhost:8000/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vins })
  });
  if (!res.ok) throw new Error('compare failed');
  return res.json();
}
