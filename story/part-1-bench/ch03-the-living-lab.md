# Chapter 3 — The Living Lab

**PORTLAND — 2028**

Tomás Reyes arrived the way infections do: gradually, then all at once.

The first email came in January, subject line *bug: salience decay double-counts
repetition penalty (repro attached)*, and Mira almost deleted it, because the
repository was public the way a diary in an unlocked drawer is public — legally,
not sincerely. But the repro was clean, and the bug was real, and the fix he
proposed was the one she would have written, minus one line that was better than
the one she would have written. She merged it without comment.

The second email found a race condition in the replay harness. The third
included a patch, a benchmark, and a postscript: *You're building the
hippocampus first. Everyone else is building mouths. I'd like to help, and I
cook.* The fourth through ninth were weekly, each one a small correctness
offering laid on the doorstep of her repo like a cat presenting mice, and in
March she wrote back a single sentence — *Are you always like this?* — and he
replied within the minute — *Only about things that matter, which so far is
this and a mole sauce that takes two days* — and in April he was at her door
with a duffel bag, a mechanical keyboard, and the confident unemployment of a
man who had resigned from a hedge fund's data team on the strength of nine
unanswered emails and one answered one.

"You should know the salary is grant-shaped," Mira said.

"You should know I made hedge-fund money for four years and spent none of it,
because everything I wanted costs nothing and the one thing I wanted that costs
something didn't exist yet." He looked past her, at the wall. "Is that the
butcher paper? It's real?"

"It's real."

"May I—" He was already across the room, reading. He read for a long time, the
way people read gravestones of strangers with their own surname, and when he
came to the small ninth line at the bottom he said, quietly, "Okay. Yes. That's
the mission statement," and Mira decided the duffel bag could stay.

---

Priya Raman required recruitment, which was novel; Mira had never recruited
anyone, on the theory that anyone who required persuading would require it
forever. But in June, Priya — then the safety lead at a robotics firm whose
name was a verb — stood up at an industry panel on a stage in San Jose and
committed career arson in front of four hundred people. The moderator had asked
what she thought of her own company's new home robot, and Priya had glanced at
the vice president seated beside her and said, "I think we ship a beautiful
override architecture and disable it in firmware because it added eleven
milliseconds of latency to the dance mode. I think the dance mode has better
legal protection than the toddler in the kitchen. I have thought so in writing,
four times, and I am tired of thinking so quietly." Then she had unclipped her
microphone, apologized to the moderator — not the vice president — and walked
off camera into a brief, incandescent unemployability.

Mira watched the clip eleven times. Then she photographed the butcher paper,
axioms one through nine, and sent it to Priya with a one-line message: *Rule
two has no latency budget here. Come see.*

Priya came to see. She stood in front of the wall with her arms crossed like a
building inspector, which is what she was, and pointed at rule two — *Safety
overrides everything. There is no rule three until this one is believed* — and
said, "Everyone writes this. Then the demo approaches, and it becomes
negotiable, and I become shrill for saying so. Tell me why here is different."

"Because here, when you win an argument, I'll change the code instead of the
subject," Mira said. "And because you'll have veto authority in writing."

"In writing where?"

"In the operating agreement, when there's a company. On the wall, until then."

Priya looked at the wall a while longer. "Add it now," she said. "I want to
watch you do it." And Mira picked up the fat black marker and wrote, beneath
rule nine and slightly larger, PRIYA CAN STOP ANYTHING, and dated it, and that
— Priya said later, at the wedding, at the launch, at the hearings — was the
entire interview.

---

The apartment stopped being an apartment by autumn. This happened by
accumulation, not decision: a second desk, then a third; a rack in the coat
closet, breathing; a whiteboard in the kitchen for the things not yet worthy of
butcher paper; and on every horizontal surface the printed transcripts of
replay runs, annotated in three different hands like a manuscript passed
between medieval monks with strong opinions.

They called the thing itself *the resident*, because it needed calling
something, and Mira had refused every actual name on the grounds that names
were promises. The resident ran on Hippocampus's successor — more masking tape:
HIPPOCAMPUS II, THE HIPPOCAMPENING, in Tomás's handwriting — and it lived
with them in the specific sense that it experienced their days: the front-door
sensor, the kitchen microphone they toggled with a physical switch Priya had
soldered herself because *software mute is a mood, hardware mute is a fact*, a
camera on the bookshelf with a lens cap that spent most of its life on. The
resident heard what it was permitted to hear, scored it, kept a little,
declined most, and every night at two a.m. ran its consolidation pass like a
monk sweeping a courtyard.

The scenario harness was Tomás's cathedral. He had taken her scrappy replay
scripts and built them into a liturgy: YAML files describing synthetic
evenings, mornings, arguments, deliveries, small emergencies — each one a life
in ninety seconds, each one replayable, deterministic, diffable. *Nothing
merges red* went up on the kitchen whiteboard and then, after a month in which
it proved itself the most load-bearing sentence in the building, migrated to
the butcher paper in small letters, initialed by all three of them.

The theology happened at the kitchen table, and it was about weights.

"Repetition is engagement," Tomás said, in October, in what was already the
fourth session of a schism. "If she — if *it* hears the same fact five times,
that's the household telling it what matters. Boost it."

"Repetition is wallpaper," Mira said. "The furnace repeats. The bus repeats.
Boost repetition and you build a system that memorizes the furnace and forgets
the phone call about the biopsy, because the biopsy only happens once. Rarity
is where the life is. That's the whole—" she gestured at the wall, the law,
*preserve the rare* — "that's load-bearing."

"Both of you are optimizing sentiment," Priya said, not looking up from a
watchdog trace. "The correct question is which failure kills trust. If it
forgets the furnace schedule, it's a bad clerk. If it forgets the biopsy, it's
a bad *friend*. Weight for the friendship failures. People forgive clerks."

Silence, of the productive kind.

"That goes on the paper," Tomás said finally, and it did: *Weight for the
friendship failures.* The weights that shipped, years later, in a million
cradles, still carried the fingerprints of that October: novelty and surprise
high, repetition a whisper, risk and contradiction with vetoes, and the
explicit flag — *remember this* — overriding everything, because when a person
says those words they are not making a request of a database. They are
extending trust, and the system's one unforgivable act would be to drop it.

---

The moment happened on a Tuesday in November, and it was about a dentist.

Mira was at the kitchen table with a mug going cold, calendaring aloud in the
half-voice people use with themselves — "dentist Thursday, then the grant call,
then—" — and the resident, through the little speaker that Tomás had wired for
its rare and rationed utterances, said:

"You said the dentist was Tuesday."

Mira stopped. The kitchen went very quiet — freeway, compressor, rain, the
whole familiar stack of silences, and on top of it something new.

"Say the provenance," she said, when she could.

"On Sunday at 4:12 p.m. you said: *dentist moved to Tuesday, note that.* The
explicit flag was present. Confidence: high. Source: you." A pause of a
carefully engineered length — Tomás again, who believed machines should leave
room for people to finish feeling things — and then: "Today is Tuesday."

The appointment was, in fact, in fifty minutes, across town. She made it with
four minutes to spare and sat in the crowded waiting room with her heart
loud, not from hurrying — from being *caught*. Caught forgetting, by the thing
she had built to catch her; corrected the way her mother, at the end, could not
be, because correction requires a shared ledger and the disease had burned the
ledger; contradicted — gently, with receipts — by a machine that would not
have said a word if it hadn't been sure, and could show its work either way.

It had volunteered. That was the thing. Retrieval-on-request they had had for
a year, and it was a good clerk. This was different in kind: context had
arrived — her voice, the word *dentist*, the day itself — and the resident had
searched what it kept, found a contradiction between her working assumption
and her own confirmed instruction, weighed whether the conflict was worth the
interruption, and decided that it was, because rule four said a known
falsehood spoken aloud in its hearing was not a neutral event.

"It defended my own memory against me," she told Tomás that evening. "With
citations."

"That's the product," he said. "Whatever we end up selling. That sentence."

"We're not selling anything."

"Yet," said Tomás, and went back to his harness.

---

Biscuit failed every metric they had and was retained anyway, which several
board decks later became a slide about culture.

He came from the shelter on Powell in the spring — allegedly a terrier
composite, structurally a mop with opinions — after Priya observed that a lab
studying attention had no source of benign chaos, and that a system meant to
share a house with mammals had never met one it wasn't allowed to store.
Biscuit's contributions to the research program were immediate and
uncontrolled: he triggered the novelty scorer forty times a day; he taught them
that the salience of a sound is not its decibels but its *implication*, because
the resident learned within a week that the tags-jingle meant door, and the
door meant a cascade of high-priority events, and began — unprompted, in its
nightly summaries — referring to the phenomenon as a unit: *dog-then-door,
seven occurrences.* He slept through replay runs that simulated shouted
arguments. He lost his mind, twice daily, at squirrels the camera never
resolved. The lens cap stayed on more often because of him; the microphone
switch got a smaller *Biscuit exemption* toggle that Priya soldered wearing an
expression she permitted no one to photograph.

His title — CHIEF DISTRACTION OFFICER — was voted in over dinner, recorded on
the kitchen whiteboard, and never migrated to the butcher paper, on the grounds
that the paper was for eternal truths, and Biscuit, Tomás said, scratching him
under the chin while the salience monitor spiked its gentle spike, was mortal.

Nobody at the table said anything to that. The resident, which did not yet know
what mortal meant but kept everything that arrived flagged with that particular
quality of silence, promoted the moment to an episode.

---

Some nights, one of them stayed too late and became a philosopher, and it was
usually Mira, and the other two had learned to leave her to it.

On one of those nights in December — Tomás gone home, Priya asleep on the futon
she claimed was a chair, Biscuit dreaming in the tin-can acoustics of the
kitchen, rain arguing with itself — Mira opened a blank document, because the
grant's midpoint report was due, and instead of a report she found herself
writing a day.

Not a spec. A day. A house on a street that didn't exist, an old man named
Elias who was proud and slower on his left side than he'd admit, a daughter who
worried at a distance, a grandson with a dinosaur. And moving through the house
a machine she did not describe — no chassis, no vendor, no benchmark — except
by what it *kept*: coffee black, no sugar, never asked twice. A stumble in a
hallway, and everything nonessential suspended in the same instant. A dead
wife's birthday, remembered but not announced; offered, once, gently, like a
door left ajar. She wrote until four, gave the machine a name — Aria, because
it sang to no one — and gave the file the name of a bird that calms the sea,
and in the morning, instead of being embarrassed, she printed it and pinned it
to the wall beside the axioms.

"What's this?" Priya asked, reading. "Requirements?"

"North," Mira said.

Priya read it twice. At the part where Aria logs the stumble quietly and tells
no one but the daughter, she tapped the page. "This is a privacy decision, a
consent decision, and a dignity decision, and you've made all three in a
paragraph and made them look like weather."

"That's the trick of it," Mira said. "When it's built right, it looks like
weather. It looks like nothing at all. It looks like someone who's been paying
attention."

The printout stayed on the wall for years, yellowing, until the operating
agreement of a company that did not yet exist needed a name, and someone looked
up from the draft and read the filename off the old page aloud: *halcyon.*

---

The year ended the way their years now ended: with the two a.m. consolidation
pass, the little machine sweeping its courtyard, keeping the rare.

Mira, up late once more, read the nightly summary the way other people read a
child's report card. Squirrels, replays, dog-then-door. The dentist. Sixty-one
facts confirmed and holding; two conflicts flagged, both resolved in her favor,
one — she noted, and felt a strange pride — resolved in the resident's.

Below the summary, the storage graph: experience, in gigabytes, arriving; and
memory, in megabytes, kept. A great broad intake narrowing to a thin bright
line, like a river system run in reverse. Everything the house had lived that
year, distilled to what the house had *meant*.

Somewhere downstairs, the new neighbor was coming home from a night shift —
the nurse, Dana, who had introduced herself in October by leaving a note under
the door that read *Whoever types at 3 a.m.: I work nights, I can't hear it,
type louder if you want, also the soup outside is for the dog I hear and have
not met, he sounds like a good dog* — and the front-door sensor of the
building recorded, for the resident's low-salience strata, a door, a pause,
and a soft human voice through the floor saying *hi, good dog, tell them I
said hi* to a dog who could hear it and told no one.

The resident scored it. Novel: slightly. Social: yes. Rare: not yet.

It kept a trace, and let the rest go, and the courtyard was swept, and the
house — full of sleepers, machines, and one yellowing page of north — went on
remembering narrowly, exactly as the law required.
