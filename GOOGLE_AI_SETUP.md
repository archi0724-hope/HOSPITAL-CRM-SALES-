# Previous Google AI setup (dashboard option removed)

**Current app:** the assistant is named **AI Assistance**. Google Gemini controls were removed from the dashboard at the user's request. Use **HOSPkart workspace**, **Provided Excel report**, or **Product catalogue & quotations**. The instructions below describe the optional server integration only; no Google connection is enabled by the dashboard.

The robot button in the bottom-right corner opens QuoteSaarthi from any dashboard page. The conversation stays open when navigating between pages. It supports keyboard close, mobile layouts and the existing quotation downloads.

## Available now

**HOSPkart workspace** is the default answer source and uses the existing Operations workspace knowledge and configured quotation catalogue. It does not automatically read the separate Meetings data held in browser storage. Google mode is a separate option for general AI questions, explanations and drafts. The workspace connection stays local and does not attach CRM data to Google requests. A separate Product catalogue & quotations option retains the quotation workflow. The robot tracks the active workspace and selected record references from View / Edit or Call note. Ask “Summarize this workspace” or “Show this lead”. Each question reads the current saved database revision; chat cannot edit records.

## Activate Google AI with a free-tier key

1. Open [Google AI Studio API keys](https://aistudio.google.com/apikey) in your own account.
2. Use a project on Google's free tier, without enabling paid billing. Create its Gemini API key. Availability and quotas depend on Google's account and regional requirements.
3. Add this line to the private `sales-ops/.env` file, preserving existing settings:

   ```dotenv
   GEMINI_API_KEY=your_private_key_here
   ```

4. Restart the localhost server, refresh the app, open the robot button and select **Google AI · Gemini**.

Do not put the key in frontend JavaScript, a workbook or chat. The server reads it from its environment. The sample `.env.example` includes an empty field; no real key is bundled.

The integration uses `gemini-2.5-flash-lite`, which is listed with free-tier text input/output in [Google's pricing](https://ai.google.dev/gemini-api/docs/pricing). It does not activate billing, use paid fallback providers or retry automatically. This server additionally caps Gemini requests at 10 per minute and 100 per rolling day, shared across users. Those local counters reset on server restart; Google's quotas and billing settings remain authoritative. A key from a billing-enabled project can incur charges even for a model that offers a free tier.

Google mode sends only the message typed into that mode and up to six recent Google-mode messages. It does not attach the CRM database, contact lists, quotation catalogue or imported workbook. Google's free-tier data terms can permit input/output to be used to improve its products; review the terms linked on its pricing page before typing sensitive information. Google mode has no live web search or CRM editing tools.

## Verification

- Eight backend tests cover configuration status without leaking credentials, missing key, CRM context exclusion, history, rate limits, timeouts, cross-origin rejection, empty responses and absence of paid fallback.
- Seventeen saved-CRM knowledge tests pass, including current-workspace selection, selected-record lookup and fresh edits without external AI calls.
- An isolated Chrome test covers the lazy robot launcher, real local CRM responses, mocked Gemini replies, quota errors, safe text rendering, history, navigation persistence, close/Escape and mobile layout. Tests use temporary databases and synthetic keys; no real Google requests were made.
- Existing integration, Sections and workbook checks pass. The standalone HTML was rebuilt; live assistance requires the localhost server.
- A real Gemini response remains unverified because no `GEMINI_API_KEY` is configured on this machine.

Backend checks: run `../.venv/Scripts/python.exe -m unittest discover -s tests -p test_google_ai.py` from `sales-ops`.
Browser check: run `.venv/Scripts/python.exe sales-ops/tests/check_robot_assistant.py` from the project root.
