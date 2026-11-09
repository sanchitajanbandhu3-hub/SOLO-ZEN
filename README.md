# Bill Shock Explainer

AI tool that makes confusing bills easy to understand. Paste any bill (hospital, hotel, phone, school fees and more) and get every charge explained in simple **English, Hindi or Marathi**, with suspicious charges flagged, a complaint message ready to send, and the answer read aloud.

Built for the **BharatCode Build League** using the BharatCode model API.

**Live demo:** https://billshockexplainer.vercel.app/ (tap "Try a sample bill")

## Screenshots

![Home page](home.png)

![Result with flagged charges](result.png)

![Hindi result](hindi.png)


## Table of contents
- [Screenshots](#screenshots)
- [Overview](#overview)
- [The problem](#the-problem)
- [The solution](#the-solution)
- [Key features](#key-features)
- [Technology stack](#technology-stack)
- [System architecture](#system-architecture)
- [Why the AI backend is decoupled](#why-the-ai-backend-is-decoupled)
- [Deployment architecture](#deployment-architecture)
- [Production services](#production-services)
- [Project structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup steps](#setup-steps)
- [Local development](#local-development)
- [Configuration](#configuration)
- [API reference](#api-reference)
- [Security and privacy](#security-and-privacy)
- [System limitations](#system-limitations)
- [Current verification status](#current-verification-status)
- [Testing and quality verification](#testing-and-quality-verification)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Disclaimer](#disclaimer)
- [Acknowledgements](#acknowledgements)
- [License](#license)

## Overview

Bill Shock Explainer is a single-page web app backed by small serverless functions. A user pastes the text of a bill, chooses a language, and receives a structured explanation: what each charge means, which charges look duplicated or unexplained, which questions to ask the company, and a polite complaint message. The explanation can also be read aloud.

## The problem

Many people pay bills without fully understanding them. Double charges, vague "adjustments" and surprise fees slip through because nobody checks every line. Bills are often only in English, so many people, especially elders, cannot read them at all.

## The solution

The app turns a pile of unclear line items into plain language. Each charge is explained in the user's own language and labelled **Looks fine**, **Ask about it** or **Looks wrong**, so people know where to look and what to ask before paying.

## Key features

- Explains every charge in plain words
- Labels each line: Looks fine / Ask about it / Looks wrong
- Lists red flags and questions to ask the company
- Writes a ready-to-send complaint message with a Copy button
- Reads the explanation aloud in English, Hindi or Marathi
- Works for any bill type (hospital, hotel, phone, school fees and more)
- Works on phones and laptops, no sign-up needed

## Technology stack

| Part | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (single page, no framework) |
| Backend | Vercel serverless functions (Node.js and Python) |
| AI model | BharatCode API, model `qwen-3.8-27b` |
| Text to speech | Python with [gTTS](https://pypi.org/project/gTTS/) |
| Hosting | Vercel |

## System architecture

```
Browser (index.html)
   |  1. user pastes bill text and picks a language
   v
POST /api/explain   (Node.js)  --->  BharatCode API (qwen-3.8-27b)
   |                                   returns structured JSON
   v
Browser renders the receipt-style result
   |  2. user taps "Listen"
   v
POST /api/speak     (Python + gTTS)  --->  MP3 audio (base64)
   |  if this fails, the browser's own speech voice is used instead
```

## Why the AI backend is decoupled

The browser never talks to the AI model directly. It calls our own serverless functions, which call the model.

- **The API key stays secret.** It lives only in a server environment variable, never in the browser or the repo.
- **The model can be swapped.** Changing the model or provider means editing one function, not the interface.
- **Features fail independently.** If audio generation fails, the written explanation still works and the app falls back to the browser's voice.
- **Input is controlled in one place.** Length limits, language checks and output parsing happen on the server.

## Deployment architecture

- The static page and the functions are deployed together on Vercel.
- Every push to the `main` branch triggers a new deployment automatically.
- `api/explain.js` runs on the Node.js runtime with a 60 second limit (set in `vercel.json`).
- `api/speak.py` runs on the Python runtime. Its dependency is listed in `requirements.txt`.
- The API key is stored as the Vercel environment variable `BHARATCODE_API_KEY`.

## Production services

| Service | Used for |
|---|---|
| Vercel | Hosting and serverless functions |
| BharatCode API | AI explanation of the bill |
| Google text-to-speech (through gTTS) | Spoken audio for the explanation |

Production endpoint: `POST https://billshockexplainer.vercel.app/api/explain`

## Project structure

```
.
├── index.html          # web page: UI and client-side JavaScript
├── api/
│   ├── explain.js      # calls the BharatCode API, returns the explanation as JSON
│   └── speak.py        # Python function that turns text into MP3 audio
├── requirements.txt    # Python dependency (gTTS)
├── vercel.json         # function settings
├── BharatCode.txt      # how this project uses BharatCode (hackathon requirement)
├── .gitignore          # keeps secrets and local files out of git
├── LICENSE
└── README.md
```

## Prerequisites

- A [BharatCode](https://bharatcode.ai) account with API access (your key is under "API access and security" on `bharatcode.ai/account`)
- A [Vercel](https://vercel.com) account (free plan is enough)
- For local development: [Node.js](https://nodejs.org/) and [Python 3](https://www.python.org/)

## Setup steps

1. Fork or clone this repository.
2. Import it at [vercel.com](https://vercel.com) (New Project).
3. Under **Environment Variables**, add `BHARATCODE_API_KEY` with your key.
4. Click **Deploy**.
5. Open the live link and tap "Try a sample bill" to confirm everything works.

## Local development

```bash
git clone https://github.com/sanchitajanbandhu3-hub/SOLO-ZEN.git
cd SOLO-ZEN
npm install -g vercel
echo "BHARATCODE_API_KEY=your_key_here" > .env.local
vercel dev
```

Open the address shown in the terminal (usually `http://localhost:3000`). The first run asks you to log in and link a project. The `.env.local` file holds your real key and must never be committed.

## Configuration

| Environment variable | Description | Required |
|---|---|---|
| `BHARATCODE_API_KEY` | Your BharatCode API key | Yes |

## API reference

### `POST /api/explain`

Request:

```json
{ "bill": "<bill text>", "language": "English" }
```

`language` is one of `English`, `Hindi`, `Marathi`. Bill text is limited to about 6,000 characters.

Response (standardized contract):

```json
{
  "bill_type": "string",
  "total": "string",
  "one_line_summary": "string",
  "charges": [
    { "name": "string", "amount": "string", "meaning": "string", "verdict": "normal | check | suspicious" }
  ],
  "red_flags": ["string"],
  "questions_to_ask": ["string"],
  "complaint_message": "string",
  "next_steps": ["string"]
}
```

Errors return `{ "error": "message" }` with status 400 (no or too little text), 405 (wrong method), 500 (server missing the key), 502 (AI service error or unreadable answer) or 503 (AI busy).

### `POST /api/speak`

Request: `{ "text": "<text to speak>", "language": "English" }`
Response: `{ "audio": "<base64 MP3>" }`, or status 502 with `{ "error": "Could not make audio" }`.

## Security and privacy

- The API key is only stored as a server environment variable. It is never sent to the browser or committed to the repository.
- This app does not store bills or keep a database.
- The bill text is sent to the BharatCode model API to generate the answer. The text to be spoken is sent to Google's text-to-speech service through gTTS.
- Results are rendered with `textContent`, not as raw HTML, so model output cannot inject scripts into the page.
- Input length is limited on the server.
- Please remove account numbers and other personal numbers before pasting a bill.
- If you ever leak your key, replace it at `bharatcode.ai/account` and update the Vercel variable.

## System limitations

- Only pasted text is supported. Photos and scanned PDFs cannot be read yet.
- The AI can be wrong or misread a bill. Results are explanations, not facts.
- It cannot look up official tariffs, rules or your provider's records.
- Audio depends on the unofficial gTTS library and Google's service. If it fails, the browser's own voice is used, and that voice may not exist for every language on every phone.
- Only English, Hindi and Marathi are supported.
- Needs an internet connection and a BharatCode API plan with access.

## Current verification status

| Item | Status |
|---|---|
| Live deployment on Vercel | Working |
| Bill explanation flow with the sample bill | Tested in English, Hindi and Marathi |
| Audio ("Listen") | Working with Python audio |
| Bills other than the sample | Tested with an electricity bill |

## Testing and quality verification

There is no automated test suite yet. Quality has been checked manually:

- Ran the sample bill in all three languages and checked the result renders correctly
- Checked the live link opens in a private browser window without a login
- Checked the page on an Android phone

Planned: automated tests for response parsing and input validation.

## Roadmap

Planned, not yet built:

- Compare two bills and show what changed
- Read bills from PDFs and photos
- A "shock score" summary for each bill
- More languages
- More sample bills (hospital, hotel, phone)
- Automated tests

## Contributing

Suggestions and bug reports are welcome through GitHub Issues. To contribute code:

1. Fork the repo and create a branch.
2. Make your change and test it with the sample bill.
3. Open a pull request describing what changed and why.

Never include API keys or private bills in issues or pull requests.

## Disclaimer

Bill Shock Explainer gives AI-generated explanations for information only. It is not legal, financial or professional advice. Always confirm important charges with your service provider before paying or disputing a bill.

## Acknowledgements

- [BharatCode](https://bharatcode.ai) for the Build League and the model API
- The Qwen model family
- [gTTS](https://pypi.org/project/gTTS/) for text-to-speech
- [Vercel](https://vercel.com) for hosting
- AI assistants were used to help write and debug code

## License

MIT License. See [LICENSE](LICENSE).

Author: SANCHITA HITENDRA JANBANDHU
