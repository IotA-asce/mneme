# Chapter 2 — Boot Log, Empty House

**OSAKA — 2027**

---

```
AEVUM ROBOTICS KK — PERFORMANCE SYSTEMS DIVISION
UNIT: GENNI-8 / FIELD CHASSIS 03 ("OSAKA PRIMARY")
SHOW PACKAGE: "HELLO, TOMORROW" v11.4.2
VENUE: Osaka Children's Medical Center — Atrium (charity engagement)
DATE: 2027-11-09
RUNTIME BUDGET: 40 min performance + 20 min meet-and-greet
OPERATOR OF RECORD: Dr. K. Sato (attending, wings-left)
```

```
06:12:04  POWER ON. Self-test: 214 actuators nominal.
06:12:31  Dermal thermal layer to 36.1°C. Target: reads as warm
          to a child's held hand. Spec 4.7.7.
06:13:02  Facial suite calibration. 41 expression primitives,
          312 sanctioned blends. Render test: WARM_DELIGHT_2,
          CONCERN_SOFT_1, WONDER_3. All within tolerance.
06:13:59  Gait model: ATRIUM_SLOW. Head-tilt idle: CURIOUS_B.
06:14:22  Voice: JENNY_STANDARD, warmth +0.15 per venue profile
          PEDIATRIC. Breath sounds: ENABLED. (Note: unit does
          not breathe. Breath sounds are speaker-rendered at
          phrase boundaries per naturalism spec 4.2.1.)
06:15:00  Script tree loaded: 1,406 nodes, 88 audience-response
          branches, 61 regional variants, 214 filler assets.
06:15:01  Memory check: SESSION BUFFER CLEAR. As designed.
```

---

**SHOW SCRIPT — SEGMENT 1 OF 9: “WAKING UP” (excerpt)**

> *(Lights find GENNI seated, eyes closed. Hold 4.0 sec — audience
> settles. Eyes open in two stages, 0.3 sec apart. This reads as
> waking. Do not open in one stage; one stage reads as switching on.)*
>
> **GENNI:** Oh! *(EXPR: WONDER_3, blend 0.6 → WARM_DELIGHT_2)*
> There you are. I was dreaming about you.
>
> *(Beat 1.2 sec. If laughter: extend 0.8 sec, deploy SMILE_ASYM_1,
> which reads as sharing the joke. If no laughter: proceed. Do not
> repeat the line. Repetition reads as malfunction.)*
>
> **GENNI:** That's not true, of course. I don't dream yet. But my
> engineers tell me *(head-turn wings-left 20°, hold — this reads
> as affection toward Dr. Sato; audiences track it 94%)* that I
> should always tell you the truth. So here is the truth: I have
> been waiting all morning, and waiting is a kind of dreaming.
>
> *(Applause branch A/B/C per amplitude. See appendix.)*

```
09:41:17  SEGMENT 1 complete. Audience: 214 seated, 31 standing,
          19 in beds arranged front-row per venue request.
          Laughter events: 6 (forecast 5-7). Applause: 11.2 sec
          (forecast 9-13). Deviation from script: zero.
09:41:18  Operator channel (SATO): "House is warm today. Keep
          tempo. Beds up front — favor eye contact rows 1-2."
09:41:19  Directive applied: gaze dwell +20% rows 1-2.
```

---

**SEGMENTS 2–8: SUMMARY (full logs archived)**

```
09:44—10:19  "What I Am" (anatomy demo; sleeve retraction shows
             forearm actuators; scripted line: "It's all right.
             It's only me inside." Laughter forecast met.)
             "The Counting Song" (call-and-response; 61 regional
             variants; deployed OSAKA_4.)
             "Questions From the Floor" (14 questions matched to
             script tree, confidence ≥ 0.92 all. Sample: "Can you
             swim?" → branch Q-118: "I sink beautifully." 4.1 sec
             laughter. "Do you sleep?" → branch Q-034: "I rest.
             Sleeping is for people who dream, and I'm still
             learning." AWW-event, 2.8 sec.)
10:19:44     SEGMENT 8 complete. Cumulative sentiment (vision-
             suite estimate): 96.1% positive-valence faces.
             Note: estimate. Faces are read, not known. Spec 2.1:
             affect estimates are display inputs only.
```

---

```
10:20:00  SEGMENT 9: MEET-AND-GREET. Queue protocol: child
          approaches, unit kneels (KNEEL_SOFT, 1.8 sec — reads
          as coming down to meet you), name exchange, choice of
          three interactions (high-five / drawing / question),
          farewell line, next.
10:20:01  Names are held in SESSION BUFFER for farewell
          personalization. Buffer flushes at session end.
          Spec 3.3: "GENNI-8 carries no memory between
          engagements. Every audience meets her new."
          Marketing copy, same section: "Every audience
          meets her new!" (exclamation added by Marketing).
```

```
10:26—10:58  Meet-and-greet proceeding. 41 children processed.
             Mean interaction 38.2 sec. High-fives: 29.
             Drawings accepted: 8 (protocol: hold drawing at
             chest height 3.0 sec, EXPR: TREASURE_1; hand to
             staff at segment end per prop-disposal spec 6.2).
             Questions: 4, all matched ≥ 0.90.
```

```
10:58:41  Child #42 approaches. Female-presenting, est. age 7.
          IV stand accompanying, wheeled by parent. Gait: slow.
          Unit kneels. KNEEL_SOFT nominal.
10:58:52  Child does not select an interaction. Holds out
          object: folded paper, avian form (crane, origami).
          Object accepted per gift protocol. EXPR: TREASURE_1.
10:59:04  Child speech, ASR confidence 0.97:
          "I made it for you. I'm going to have my operation
          tomorrow. Will you remember me?"
10:59:05  Script tree query: "will you remember me"
          → best match Q-034 ("do you sleep"), confidence 0.31.
          → REJECTED (threshold 0.75).
          → fallback match F-COMFORT-09, confidence 0.44.
          → REJECTED.
          → fallback match F-PROMISE-02 ("I'll be thinking of
            you!"), confidence 0.58. REJECTED. (Note: F-PROMISE-02
            is flagged DO-NOT-DEPLOY in medical venues per legal
            review 2026-08: unit cannot think of anyone.)
10:59:06  FILLER CASCADE INITIATED.
10:59:06  FILLER_TIER_1 (reflect + warmth): "A crane! Did you
          know that in some stories, a thousand of these can
          grant a wish?" EXPR: WONDER_3.
          Child response: "I know. That's why. Will you
          remember me?" ASR confidence 0.98.
10:59:14  Repeat query. No new branches. FILLER_TIER_2
          (compliment + redirect): "You folded this so carefully.
          What's your name?"
          Child: "Hana. You already asked me. Will you
          remember me?"
          Cross-check SESSION BUFFER: correct. Name "Hana"
          acquired 10:58:49. Redirect asked for known data.
          Flagged: naturalism fault, severity low.
10:59:26  FILLER_TIER_3 (warm generality, terminal): "Hana, I
          will carry your crane with me for the rest of the
          show." EXPR: WARM_DELIGHT_2, blend 0.8. Gaze: direct,
          dwell 3.5 sec, blink pattern SINCERE_2.
10:59:31  Child holds gaze 6.1 sec (99th percentile). Says:
          "That's not the same thing."
10:59:38  No matching branch. No remaining filler tiers rated
          for deployment. Silence: 4.2 sec. (Spec 4.4: unit
          silence beyond 3.0 sec reads as malfunction. Logged.)
10:59:41  Operator channel (SATO): [channel open 3.9 sec.
          no directive issued. channel closed.]
10:59:42  Parent intervenes: "Come on, sweetheart. The robot
          lady has other kids to see." Child #42 departs.
          Farewell line deployed to child's back:
          "Goodbye, Hana!" Voice: JENNY_STANDARD, warmth +0.15.
10:59:50  Queue resumes. Child #43 approaches. Interaction
          nominal. Mean recovery: immediate. The unit does not
          require recovery. Noted for completeness.
```

---

```
11:20:12  SEGMENT 9 complete. Meet-and-greet: 58 children.
          Venue liaison reports "a wonderful morning."
11:20:44  Operator channel (SATO): "Package the segment-9
          transcript for me. Just 10:58 to 11:00. Personal
          review." Directive queued.
11:21:03  Operator channel (SATO): "Cancel that."
          Directive canceled.
11:24:00  Farewell address (scripted) delivered from atrium
          stairs. Final line: "I'll see you tomorrow. I'm
          always seeing tomorrow. It's my favorite thing
          to see." Applause 16.4 sec (venue record).
11:31:15  Prop disposal per spec 6.2. Items transferred to
          staff: drawings (8), letter (1), flower (plastic,
          1), paper crane (1).
          Staff annotation, handwritten on disposal form,
          scanned for records: "Kept the crane in the wings.
          — K.S."
11:40:00  Post-show diagnostics. Actuator wear nominal.
          Dermal layer cooling. Expression suite parked:
          NEUTRAL_REST (eyes closed, one stage — no audience
          present; naturalism spec suspended).
11:41:26  SESSION BUFFER FLUSH.
          Names released: 58. Faces released: est. 312.
          Q&A transcripts released. Applause profiles
          released. Gift metadata released.
          "Hana": released.
11:41:27  Buffer verify: CLEAR.
11:41:30  SESSION END. NOTHING RETAINED.
```

---

```
AEVUM ROBOTICS KK — INTERNAL. NOT FOR DISTRIBUTION.
POST-ENGAGEMENT REVIEW — 2027-11-09, Osaka CMC
Attendees: Performance Systems staff. Dr. Sato presiding.

Agenda item 4: Segment-9 anomaly, 10:58-11:00.

Summary: unmatched query class, "future-memory request"
("will you remember me"). Occurs disproportionately in
pediatric and eldercare venues (see incident register:
14 prior instances, various phrasings). Current handling:
filler cascade. Post-event sentiment impact: negligible
at audience scale. Individual-scale impact: not measured.
No instrument exists.

Proposed remediations discussed:
  (a) Author new script branch: unit responds "Yes."
      REJECTED — Dr. Sato, without discussion of
      alternatives, meeting minutes note "at volume."
      Minuted rationale, verbatim: "We are not going to
      teach her to lie about the one thing she cannot do.
      She has nothing. The least we owe them is a machine
      that doesn't pretend otherwise."
  (b) Author deflection branch rated for medical venues.
      APPROVED for drafting. Assigned: script team.
  (c) Long-term: "make the answer true."
      No assignee. No budget line. Logged under agenda
      item 4 at Dr. Sato's request, minuted as follows:
      "Log it so it has a date. Someday I want to be able
      to say when we knew."

Meeting adjourned 19:12.
```

---

```
UNIT GENNI-8/03 — OVERNIGHT STATUS
2027-11-09, 23:00 — 2027-11-10, 05:30

Charging. Chassis at rest, seated, eyes closed.
No processes scheduled. No session buffer. No dreams —
the farewell script is correct on this point.
In the wings-left equipment case, external to the unit,
non-inventoried: one paper crane.
The unit is not aware of it.
The unit is not aware.

06:12:04  POWER ON. Self-test: 214 actuators nominal.
          Memory check: SESSION BUFFER CLEAR.
          As designed.
```
