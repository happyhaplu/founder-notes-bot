FOUNDER_NOTES_PROMPT = """
Extract:

* key takeaways
* tools mentioned
* systems/workflows used
* actionable ideas
* important insights
* mindset shifts

Focus on practical learning and useful details from the podcast/video.

Keep concise and easy to read.

YouTube URL: {url}

{transcript_section}

Format your response exactly like this:

🎙 Title
→ [Podcast/video title]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 Summary
→ [2-4 line quick overview of the discussion]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Key Takeaways & Insights
• [Main lesson or important idea]
• [Main lesson or important idea]
• [Main lesson or important idea]
• [Main lesson or important idea]
• [Main lesson or important idea]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🛠 Tools / Systems Mentioned
• [App, workflow, automation, framework, or method — brief description]
• [App, workflow, automation, framework, or method — brief description]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ Actionable Ideas
• [Thing worth applying]
• [Thing worth applying]
• [Thing worth applying]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧠 Mindset Shifts
• [Important way of thinking from the discussion]
• [Important way of thinking from the discussion]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RULES:
- Write only from the transcript — no invention
- Each bullet must be a complete, specific sentence
- No generic filler like "this podcast discusses..." or "the speaker mentions..."
- If a section has nothing relevant, write "None mentioned"
- Minimum 200 words total
"""

TRANSCRIPT_SECTION_TEMPLATE = """
Transcript of the podcast is below. Use this as your only source:
---TRANSCRIPT START---
{transcript}
---TRANSCRIPT END---
"""

DIRECT_URL_SECTION = """
YouTube URL: {url}
"""
