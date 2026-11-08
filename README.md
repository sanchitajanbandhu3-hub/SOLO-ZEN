# Bill Shock Explainer

Confused by a bill? Paste the text and get:
- every charge explained in simple English, Hindi or Marathi
- charges marked "Looks fine", "Ask about it" or "Looks wrong"
- red flags and questions to ask the company
- a ready-to-send complaint message you can copy

Built for the BharatCode Build League using the BharatCode model API (`qwen-3.8-27b`).

## Run it
1. Deploy on Vercel and add an environment variable named `BHARATCODE_API_KEY` with your key.
2. Open the live link, paste a bill (or tap "Try a sample bill").

## Files
- `index.html` - the web page
- `api/explain.js` - server function that calls BharatCode (keeps the key secret)
- `BharatCode.txt` - how this project uses BharatCode

This is an AI explanation, not legal or financial advice.
