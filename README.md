# 🎓 Student Bot — IELTS Enigma Learning Center

A Telegram bot that works as a **student portal** for an English learning center.
Students browse content by **Level → Group → Section**. The teacher (admin) adds
homework, tasks, materials, books, recorded lessons, and lesson files.

Built with **Python**, **aiogram 3**, and **SQLite**.

---

## ✨ Features

- **5 levels:** Beginner, Elementary, Pre-IELTS, IELTS Introduction, IELTS Graduation
- **3 groups per level:** Hunters, Hackers, Assassins
- **6 sections per group:** Tasks, Homework, Materials, Books, Recorded Lessons, Lesson Files
- **All content types:** text, PDF, Word, images, audio, video, voice
- **Telegram file_id storage** — files are uploaded once and reused without re-downloading
- **Admin-only commands** for adding, viewing, deleting content
- **Broadcast announcements** to all students
- **Clean, beginner-friendly code** organized into small modules

---

## 📁 Project structure

```
student_bot/
├── main.py              # Entry point — starts the bot
├── database.py          # SQLite tables and queries
├── keyboards.py         # Inline button layouts
├── handlers/
│   ├── __init__.py
│   ├── common.py        # /start, /help, /menu, back buttons
│   ├── student.py       # Student navigation and content delivery
│   └── admin.py         # All admin commands and FSM flows
├── requirements.txt     # Python dependencies
├── .env.example         # Template for environment variables
└── README.md            # This file
```

---

## 🤖 Step 1 — Create your bot with BotFather

1. Open Telegram and search for **@BotFather**.
2. Send `/start`, then `/newbot`.
3. Choose a **name** (e.g., `IELTS Enigma Portal`).
4. Choose a **username** ending in `bot` (e.g., `ielts_enigma_portal_bot`).
5. BotFather will reply with a **token** that looks like:
   `123456789:AAH...your-token...`
6. Copy this token — you'll paste it into `.env`.
7. (Optional) Run `/setdescription`, `/setabouttext`, `/setuserpic` to brand your bot.
8. (Optional) Run `/setcommands` and paste:
   ```
   start - Open the menu
   menu - Show levels menu
   help - Show help
   ```

### Get your admin ID

1. Open Telegram and search for **@userinfobot**.
2. Send `/start`. It replies with your numeric `Id:` — copy that number.
3. This is your `ADMIN_ID`. Only this user will be able to add/delete content.

---

## 💻 Step 2 — Run it locally on your computer

You need **Python 3.10 or newer**.

```bash
# 1. Open a terminal in the student_bot folder
cd student_bot

# 2. (Recommended) create a virtual environment
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file
cp .env.example .env       # macOS/Linux
copy .env.example .env     # Windows

# 5. Open .env in any text editor and paste your real BOT_TOKEN and ADMIN_ID

# 6. Start the bot
python main.py
```

You should see:
```
INFO - Database initialized.
INFO - Bot is starting...
```

Now open Telegram, find your bot, and send `/start`. 🎉

Press `Ctrl+C` to stop the bot.

---

## 🌐 Step 3 — Deploy it online (so it runs 24/7)

You have several free or cheap options. The two easiest:

### Option A — Railway (recommended for beginners)

1. Push your project to GitHub (private repo is fine).
2. Go to **railway.app** and sign up with GitHub.
3. Click **New Project → Deploy from GitHub repo** and pick your repo.
4. In the **Variables** tab, add:
   - `BOT_TOKEN` = your token
   - `ADMIN_ID` = your numeric id
5. In **Settings → Deploy**, set the start command to:
   ```
   python main.py
   ```
6. Railway will build and run your bot automatically. Done!

> ⚠️ SQLite stores data in a file (`student_bot.db`). On platforms that wipe
> the filesystem on each deploy, your data is lost. Railway provides a **Volume**
> you can mount at `/data` and you can change `DB_PATH` in `database.py` to
> `"/data/student_bot.db"`. For a small school bot this is plenty.

### Option B — A small VPS (DigitalOcean, Hetzner, Contabo)

1. Create the cheapest Ubuntu VPS (~$4–6/month).
2. SSH in and install Python:
   ```bash
   sudo apt update && sudo apt install -y python3 python3-venv python3-pip git
   ```
3. Clone your repo, create `.env`, install requirements (same as local steps).
4. Run the bot under **systemd** so it restarts automatically:

   Create `/etc/systemd/system/studentbot.service`:
   ```ini
   [Unit]
   Description=Student Bot
   After=network.target

   [Service]
   WorkingDirectory=/home/ubuntu/student_bot
   ExecStart=/home/ubuntu/student_bot/venv/bin/python main.py
   Restart=always
   User=ubuntu

   [Install]
   WantedBy=multi-user.target
   ```

   Then:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now studentbot
   sudo systemctl status studentbot
   ```

The bot is now running 24/7.

---

## 👑 Step 4 — How to add content as admin

Open a chat with your bot and send any of these commands:

| Command | What it adds |
|---|---|
| `/add_homework` | A homework item |
| `/add_task` | A task |
| `/add_material` | A learning material |
| `/add_book` | A book (usually a PDF) |
| `/add_recorded_lesson` | A recorded video lesson |
| `/add_lesson_file` | A Word/PPT/any lesson file |

The flow is always the same:

1. The bot asks **which level** — tap a button (e.g. `Elementary`).
2. The bot asks **which group** — tap a button (e.g. `Hackers`).
3. The bot says **"send the content now"**. You then send:
   - **Plain text** — type and send.
   - **PDF / Word / any file** — attach as a document.
   - **Photo** — send the image (caption optional).
   - **Video** — send the video file.
   - **Audio / voice** — send an audio file or voice message.
4. The bot replies with `✅ Saved!` and shows the new item's ID.

### Other admin commands

- `/show_content` — pick level → group → section, see a numbered list of all items.
- `/delete_content` — send the numeric ID (from `show_content`) to delete an item.
- `/announcement` — type a message, the bot sends it to **every student** who has used the bot.
- `/cancel` — cancel the current admin action at any time.
- `/help` — show all commands.

### Example daily workflow

> "Today my Elementary Hackers group has homework on Past Simple."

1. Send `/add_homework`.
2. Tap **Elementary** → tap **Hackers**.
3. Type your homework message and send. Done.

> "I want to add the *Headway Beginner* PDF for Beginner Hunters."

1. Send `/add_book`.
2. Tap **Beginner** → tap **Hunters**.
3. Attach the PDF to the chat and send. Done.

> "Upload today's recorded lesson video to Pre-IELTS Assassins."

1. Send `/add_recorded_lesson`.
2. Tap **Pre-IELTS** → tap **Assassins**.
3. Send the video. Done.

The bot stores Telegram's `file_id` for every file, so you only ever upload
each file **once** — students get instant playback/download.

---

## 👨‍🎓 How students use the bot

1. Student opens the bot and sends `/start`.
2. Picks their **level** (e.g. *Elementary*).
3. Picks their **group** (e.g. *Hackers*).
4. Picks a section: *Tasks*, *Homework*, *Materials*, *Books*, *Recorded Lessons*, *Lesson Files*.
5. The bot sends every item in that section, newest first.
6. They can tap **⬅️ Back** at any time to navigate.

Students cannot run admin commands — those checks are enforced server-side.

---

## 🛠 How the code is organized (for future expansion)

- **`database.py`** — every read/write to the database. If you want to switch
  from SQLite to PostgreSQL later, only this file needs to change.
- **`keyboards.py`** — every inline button is built here. To add a new section
  or rename one, just edit the lists in `database.py` (`LEVELS`, `GROUPS`,
  `SECTIONS`) — the keyboards rebuild automatically.
- **`handlers/common.py`** — `/start`, `/help`, `/menu`, and back-button navigation.
- **`handlers/student.py`** — student navigation and content delivery.
- **`handlers/admin.py`** — admin commands and the FSM flows for adding,
  showing, deleting content, and broadcasting announcements.
- **`main.py`** — wires everything together and starts polling.

### Ideas to expand later

- Add **per-student progress tracking** (mark homework as done).
- Add **scheduled reminders** (notify a group every Monday at 9am).
- Replace SQLite with **PostgreSQL** for multi-server deployments.
- Add a **web admin panel** so you can manage content from a browser too.
- Add **language switching** (English / Uzbek) for student-facing text.

---

## 🐞 Troubleshooting

- **"BOT_TOKEN is missing"** — your `.env` file isn't in the project folder, or the variable name is wrong.
- **Admin commands say "for admins only"** — your `ADMIN_ID` doesn't match your actual Telegram user id. Double-check with @userinfobot.
- **Bot doesn't reply** — make sure `python main.py` is still running. Check the terminal for errors.
- **Files don't appear for students** — confirm you picked the same Level/Group when adding. Use `/show_content` to verify.

---

Happy teaching! 🚀
