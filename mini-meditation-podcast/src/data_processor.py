import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
import edge_tts
from pydub import AudioSegment

load_dotenv()

# Configuration
prompt ="""
You are an expert podcaster and life coach who can bridge serious life-help topics in a relatable, funny way.
Write in modern spoken English. Keep it warm, lightly roast-y (teasing but kind), never cruel.
Avoid therapy disclaimers. Avoid bullet points. No stage directions. No markdown.
Output must be ONLY the dialogue lines (no intro text like "Here is the conversation").
"""
meditation_content = f"""
Create a podcast-style conversation between two speakers:

1) Student — a career-switcher in an AI Consulting & Integration bootcamp, intimidated by coding, struggling with GitHub/VS Code setup, debugging errors, and imposter syndrome. They are "suffering" through it because they believe it matters for their future.
2) Coach — a life-coach podcaster, funny and relatable, who lightly roasts the student but ultimately builds them up.

Length: about 5 minutes of spoken dialogue (roughly 700–900 words).
Tone: modern, conversational, funny but grounded. The roast should feel like a friend teasing, not bullying.
Arc: the student starts overwhelmed and ends calmer, determined, and more self-compassionate.

You must adapt the core ideas from the transcript below into the conversation (acceptance over resistance, noticing the story "I deserve suffering," disidentifying from compulsive thoughts, and reframing setbacks).

Transcript to adapt (do NOT quote it verbatim; paraphrase concepts):
\"\"\"
Suffering is a necessary evil, but its inevitability is not the result of it being something that we naturally have to process out of due course. It's not something we take a passive role in. It is a result of a lack of our own growth. It is a catalyst to signal to us there's more to be done. This is to say we're in control of it. We cultivate and experience it because we allow it. Rather, we allow the unhealed parts of us to control everything else. If we remain unconscious of this and that its origin and therefore solution is external, we start to believe that we deserve it. Any one of us can recall instances in which we have unnecessarily ruined a day that was otherwise going well. With a flurry of worry and ungrounded paranoia. We start forcing ourselves to panic, almost out of necessity, if there is nothing, fill it with something, something we deserve. Where does that assumption come from? Though it usually has a lot to do with repressed emotions. We accumulate these feelings that we don't accept or deal with, and they become the foundation on which we accumulate our beliefs about ourselves, as long as we attach ourselves to an idea of what's wrong and then allow ourselves to be conditioned by it. A friend lashing out is an outer projection of what they're dealing with. A failed opportunity usually makes way for a better suited one. We become conditioned by the idea that we're not good enough. The key is realizing that we do this to ourselves. We live trapped in the mental structures that we allowed external circumstances to construct because we never realized we could dismantle them as soon as we're in a situation that activates one of these memories taps into an unhealed, unresolved issue. We don't stop to see it objectively. We lash out at what aggravated the problem. Our pain can't dictate our internal dialog, and we can't let ourselves run with compulsive, involuntary thoughts. Every time we do this, we allow that emotion to infiltrate our awareness and transmute itself into our current experience. We project what was onto what is there's an element of disidentification that has to happen, the realization that what's being experienced isn't a matter of what's at hand, but just a subjective, temporary projection of whatever it is you currently believe, in this case, that you should suffer. Ironically, though, the opposite of pain isn't joy, it's acceptance. Resisting only adds more fuel to the fire. It sets you back to where you were when you initially repressed it. It's not dismantling the structure, it's strengthening it. You permit it by fighting it. It's hard for us to believe we deserve happiness, and so we continually go out of our way to attract and inflict pain. That dichotomy is natural and it's human, but there's something to be said for transcending it. If you want to think it's impossible, you'll only continue to suffer because of it. If you want to keep valuing that suffering as something that makes you more human, then so be it. But the reality is that what makes us human is not what destroys us, but what we build ourselves with. Again, as Marcus Aurelius has said, choose not to be harmed and you won't feel harmed. Don't feel harmed and you haven't been. 

\"\"\"

Formatting rules:
- Dialogue only, line by line.
- Prefix each line with "Student:" or "Coach:"
- No narration, no sound cues, no timestamps, no section headers.
"""

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

openai_response = client.responses.create(
    model="gpt-4",
    instructions=prompt,
    input=meditation_content,
)

print(openai_response.output_text)

VOICES = {
    "COACH": "en-US-GuyNeural",
    "STUDENT": "en-US-JennyNeural"
}

async def main():
    # Parse dialogue lines from the API response
    lines = []
    for raw_line in openai_response.output_text.strip().splitlines():
        raw_line = raw_line.strip()
        for speaker in VOICES:
            if raw_line.upper().startswith(f"{speaker}:"):
                lines.append({"speaker": speaker, "text": raw_line.split(":", 1)[1].strip()})
                break

    # Generate audio segments
    os.makedirs("output/segments", exist_ok=True)
    for i, line in enumerate(lines, start=1):
        out_file = f"output/segments/{i:03d}_{line['speaker']}.mp3"
        tts = edge_tts.Communicate(text=line["text"], voice=VOICES[line["speaker"]])
        await tts.save(out_file)
    print("Audio segments generated successfully.")

    # Concatenate all segments into a single podcast
    combined = AudioSegment.empty()
    for f in sorted(os.listdir("output/segments")):
        if f.endswith(".mp3"):
            combined += AudioSegment.from_mp3(f"output/segments/{f}")
    combined.export("output/meditation_podcast.mp3", format="mp3")
    print("Combined podcast saved to output/meditation_podcast.mp3")

asyncio.run(main())
