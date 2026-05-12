# Padlet Post + 3-Minute Presentation Script

This file is for your own reference — it's NOT part of the program submission.

---

## Padlet Post (~100 words)

**Title:** USYD Survival Simulator — Can You Make It Through One Semester?

**Image idea:** A pixel-style splash showing the dashboard with progress bars
in different colours, plus the four COMP/INFO course codes. (You can take a
screenshot of the running game's title screen — Rich's coloured panels look
great in screenshots.)

**Description (98 words):**

> Welcome to USYD Survival Simulator — a text-based life sim where you play a
> postgrad CS student trying to survive 13 weeks of classes plus 2 weeks of
> exams. Each morning you allocate eight hours across study, part-time work,
> rest, and food. Random events hit daily: train delays, group-project drama,
> Manning Bar pizza, late-night IGA price hikes. Balance energy, health, money,
> and four separate course progress bars to unlock one of nine endings — from
> First Class Honours to bankruptcy at Newtown Station. Built with Python and
> Rich. Target audience: every USYD student who has ever pulled an all-nighter.

---

## 3-Minute Presentation Script

Total time: 180 seconds. Aim for ~30 words per 10 seconds (~540 words total).

### 0:00 – 0:20 — Hook (~60 words)
> "Show of hands — who has ever pulled an all-nighter at Fisher Library?
> Who has eaten instant noodles three nights in a row because rent was due?
> If that's you, you're already 60% qualified to play my game.
> It's called USYD Survival Simulator, and the goal is to make it through
> one full semester without dying, going bankrupt, or dropping out."

### 0:20 – 0:50 — What is it (~90 words)
> "It's a text-based life simulation. You play a postgrad CS student — me, basically.
> Each morning, you have eight hours of active time. You decide how to split it
> across studying for your four courses, working part-time jobs, resting, and eating.
> The four jobs are cafe waiter, high-school tutor, dev intern, and research assistant —
> each grows a different skill, and skill level determines pay rate. Random events
> fire daily. Some are good, some are very bad."

### 0:50 – 1:30 — Demo (~120 words)
> *(Live demo — show the dashboard.)*
> "Here's the dashboard. On the left, my core stats — energy, health, money. On
> the right, my four courses. Skills and event log along the bottom. Right now
> I'm in week 5, day 3.
>
> *(Pick the 'Balanced' preset.)* The game lets me pick from four preset plans
> for fast play, or go fully custom. Watch the bars move as I execute the day.
>
> *(Trigger an event.)* That's a random event — my flatmate had a party last
> night, and my energy just took a hit. Welcome to share housing in Sydney."

### 1:30 – 2:30 — The interesting parts (~150 words)
> "There are nine endings. The obvious ones are Honours, plain Pass, Dropout,
> and Bankruptcy. But there are also some hidden ones.
>
> If you take a part-time RA position with a professor for at least 30 days,
> keep your grades above 80, and impress her enough — you unlock the
> Full Scholarship PhD ending.
>
> There's a lottery ticket event with a 0.5% win rate. If you hit it, you
> stop caring about the rest of the semester. Hidden ending.
>
> And then there's the dark ending — if you abuse stimulants more than 20
> times trying to keep your energy up, you don't graduate. You become a
> cautionary tale.
>
> Under the hood, the game uses 9 advanced Python concepts including class
> inheritance, decorators for logging, JSON file I/O for saves, and the Rich
> library for the terminal dashboard."

### 2:30 – 3:00 — Close (~80 words)
> "I built this in about 7 hours. The events database is in a JSON file so
> anyone can add new events without touching the code — IT Project Management
> taught me to be lazy about hard-coding.
>
> Honestly, the most fun part of playtesting was watching how often I
> bankrupted my own character. Maybe that says something about the
> Sydney rental market. Thanks for listening — please vote!"

---

## Demo Tips

1. **Practice the demo path.** During the live demo, you will be picking from
   menus on stage. Plan the exact 3-4 inputs you want to make so you don't
   freeze up.
2. **Pre-warm the dashboard.** Start with a save file at week 5–6, where the
   stats are partially filled and the courses look meaningful. A blank week-1
   board is less impressive than a mid-semester one.
3. **Trigger an interesting event live.** If possible, set up the random
   seed (or play a few times) so a memorable event fires during the demo.
4. **Show a hidden ending in the slides.** You don't have time to play to a
   hidden ending live, but you can flash a screenshot of one (e.g. the
   PhD ending text) on the screen for 10 seconds.
5. **Voice over the dashboard.** Don't read the bars — describe what they
   *mean*. "I'm completely broke right now, and the rent is due tomorrow…"

---

## Items to do for submission

- [ ] Code Submission slide on Ed (zip the `usyd_survival/` folder)
- [ ] Padlet post on tutor's board (title + image + description)
- [ ] Take a screenshot of the title screen + dashboard for the Padlet image
- [ ] Practice the 3-minute presentation 2-3 times before tutorial
- [ ] Confirm the project is approved by your tutor before week 8

---

## Possible Tutor Approval Pitch (Email Template)

> Subject: COMP9001 Final Project — Idea Approval
>
> Hi [Tutor Name],
>
> I'd like to get your sign-off on my final project idea before I start
> building it. The project is a text-based life simulation game called
> USYD Survival Simulator. The player runs a postgrad CS student through
> one semester (13 study weeks + 2 exam weeks), allocating their daily
> hours across studying, part-time work, rest, and food, while random
> events affect their energy, money, health, and academic progress.
>
> The game has 9 distinct endings (including 2 hidden ones) and uses the
> Rich library for a coloured terminal dashboard. Advanced concepts I'll
> demonstrate include OOP / inheritance, decorators, JSON file I/O,
> exception handling, list comprehensions, and lambda expressions.
>
> Estimated effort: ~7 hours. Happy to chat through any concerns.
>
> Thanks,
> Champ
