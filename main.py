import discord
from discord.ext import tasks, commands
from datetime import datetime, timedelta
import asyncio
import os
from dotenv import load_dotenv
from routine_data import combined_routine, subject_map, type_map

# Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

GROUP_C_ROLE_ID = int(os.getenv("GROUP_C_ROLE_ID"))
GROUP_D_ROLE_ID = int(os.getenv("GROUP_D_ROLE_ID"))
CLASS_ROLE_ID = int(os.getenv("CLASS_ROLE_ID"))

print("🔑 TOKEN loaded:", TOKEN[:10] + "..." if TOKEN else "❌ Not found")
print("📢 CHANNEL_ID loaded:", CHANNEL_ID)
print("👥 Role IDs loaded:", GROUP_C_ROLE_ID, GROUP_D_ROLE_ID, CLASS_ROLE_ID)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# To keep track of sent notifications to avoid repeats
notified_classes = set()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await asyncio.sleep(1)
    check_schedule.start()

def parse_time_range(time_range: str) -> datetime.time:
    start_time = time_range.split(" - ")[0]
    return datetime.strptime(start_time, "%H:%M").time()

@bot.command()
async def test(ctx):
    await ctx.send("✅ Bot is working!")

@tasks.loop(minutes=1)
async def check_schedule():
    global notified_classes
    try:
        now = datetime.now()
        today = now.strftime("%A")

        # Clean old notifications for previous days
        notified_classes = {entry for entry in notified_classes if entry[0] == today}

        for entry in combined_routine.get(today, []):
            entry_start_time = parse_time_range(entry["time"])
            class_datetime = datetime.combine(now.date(), entry_start_time)
            #reminder_datetime = class_datetime - timedelta(minutes=15)
            reminder_datetime = now

            # Notify if current time is within ±60 seconds of reminder time
            if abs((now - reminder_datetime).total_seconds()) <= 60:
                notification_key = (today, entry["time"])

                if notification_key in notified_classes:
                    continue  # Already notified

                # Determine subjects and types for both groups
                if isinstance(entry["subject"], dict):
                    subj_c = entry["subject"].get("C")
                    subj_d = entry["subject"].get("D")
                    type_c = type_map.get(entry["type"].get("C"))
                    type_d = type_map.get(entry["type"].get("D"))
                else:
                    subj_c = subj_d = entry["subject"]
                    type_c = type_d = type_map.get(entry.get("type"))

                # Skip if both groups have BREAK
                if subj_c == "BREAK" and subj_d == "BREAK":
                    continue

                channel = bot.get_channel(CHANNEL_ID)
                if not channel:
                    print("❌ Failed to fetch channel.")
                    return

                # Compose and send notifications
                if subj_c == subj_d:
                    # Same subject and type for both groups (and not BREAK)
                    if subj_c != "BREAK":
                        subject_name = subject_map.get(subj_c, subj_c)
                        msg = (
                            f"<@&{CLASS_ROLE_ID}> ⏰ **Upcoming {type_c} in 15 minutes!**\n"
                            f"📚 {subject_name} at {entry['time']}"
                        )
                        await channel.send(msg)
                        print(f"✅ Sent combined notification for both groups: {subject_name} at {entry['time']}")
                else:
                    # Different classes for groups
                    if subj_c != "BREAK":
                        subject_name_c = subject_map.get(subj_c, subj_c)
                        msg_c = (
                            f"<@&{GROUP_C_ROLE_ID}> ⏰ **Upcoming {type_c} in 15 minutes!**\n"
                            f"📚 {subject_name_c} at {entry['time']}"
                        )
                        await channel.send(msg_c)
                        print(f"✅ Sent notification for Group C: {subject_name_c} at {entry['time']}")

                    if subj_d != "BREAK":
                        subject_name_d = subject_map.get(subj_d, subj_d)
                        msg_d = (
                            f"<@&{GROUP_D_ROLE_ID}> ⏰ **Upcoming {type_d} in 15 minutes!**\n"
                            f"📚 {subject_name_d} at {entry['time']}"
                        )
                        await channel.send(msg_d)
                        print(f"✅ Sent notification for Group D: {subject_name_d} at {entry['time']}")

                notified_classes.add(notification_key)

    except Exception as e:
        print(f"❌ Error in check_schedule: {e}")

bot.run(TOKEN)
