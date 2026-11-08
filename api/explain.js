// Runs on the server (Vercel). The secret API key never reaches the browser.
const SYSTEM = `You are Bill Shock Explainer, a careful assistant that helps ordinary people in India understand confusing bills (electricity, phone, internet, hospital, gas, school fees, credit card).

Read the bill text and reply with ONLY one JSON object, no markdown, no extra words:
{
  "bill_type": "short name of the bill",
  "total": "total amount payable exactly as written, or 'Not clear'",
  "one_line_summary": "one plain sentence on what this bill is and what to do",
  "charges": [
    {"name": "charge name", "amount": "amount as written", "meaning": "what this charge is, in simple words", "verdict": "normal" | "check" | "suspicious"}
  ],
  "red_flags": ["things that look wrong, duplicated, vague or unusually high"],
  "questions_to_ask": ["specific questions to ask the company"],
  "complaint_message": "a polite, ready-to-send message disputing the unclear charges. Use placeholders like [Your name] and [Account number].",
  "next_steps": ["2 to 4 short practical steps, including any deadline seen in the bill"]
}

Rules:
- Never invent numbers or facts. Use only what is in the bill. If something is unclear, say it is unclear.
- Use "suspicious" only when a charge looks duplicated, contradicts the bill, or has no explanation. Say why in "meaning". Use "check" for charges worth asking about.
- If the text is not a bill, return charges as an empty list and explain in one_line_summary.
- Keep JSON keys in English. Write all values in the language the user asks for, using very simple words.
- You are not a lawyer. Do not give legal advice.`;

module.exports = async (req, res) => {
  if (req.method !== "POST") {
    res.status(405).json({ error: "Use POST." });
    return;
  }
  const key = process.env.BHARATCODE_API_KEY;
  if (!key) {
    res.status(500).json({ error: "Server is missing BHARATCODE_API_KEY." });
    return;
  }
  const body = req.body || {};
  const bill = String(body.bill || "").trim().slice(0, 6000);
  const language = ["English", "Hindi", "Marathi"].includes(body.language) ? body.language : "English";
  if (bill.length < 20) {
    res.status(400).json({ error: "Please paste the full text of your bill." });
    return;
  }

  try {
    const r = await fetch("https://bharatcode.ai/api/model/v1/chat/completions", {
      method: "POST",
      headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: "qwen-3.8-27b",
        messages: [
          { role: "system", content: SYSTEM },
          { role: "user", content: "Reply language: " + language + "\n\nBILL TEXT:\n" + bill }
        ],
        max_tokens: 4000,
        reasoning_effort: "none",
        temperature: 0.2
      })
    });
    if (r.status === 503) {
      res.status(503).json({ error: "The AI is busy. Wait a few seconds and try again." });
      return;
    }
    if (!r.ok) {
      res.status(502).json({ error: "The AI service returned an error (" + r.status + ")." });
      return;
    }
    const data = await r.json();
    const text = (data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) || "";
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start === -1 || end === -1) throw new Error("No JSON in reply");
    res.status(200).json(JSON.parse(text.slice(start, end + 1)));
  } catch (e) {
    res.status(502).json({ error: "Could not read the AI's answer. Please try again." });
  }
};
