const GITHUB_OWNER = "blacksinisterx";
const GITHUB_REPO = "Ai-UX-Auditor";
const WORKFLOW_FILE = "audit.yml";

export async function POST(request: Request) {
  const { auditId } = await request.json();
  if (!auditId || typeof auditId !== "string") {
    return Response.json({ error: "auditId is required" }, { status: 400 });
  }

  const token = process.env.GITHUB_DISPATCH_TOKEN;
  if (!token) {
    return Response.json({ error: "Dispatch not configured" }, { status: 500 });
  }

  const res = await fetch(
    `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/actions/workflows/${WORKFLOW_FILE}/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ ref: "main", inputs: { audit_id: auditId } }),
    },
  );

  if (!res.ok) {
    const body = await res.text();
    return Response.json({ error: `GitHub dispatch failed: ${body}` }, { status: 502 });
  }

  return Response.json({ ok: true });
}
