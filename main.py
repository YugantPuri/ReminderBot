import discord
from discord.ext import tasks, commands
from discord.ui import View, Select
from datetime import datetime, timedelta
import asyncio
import os
from dotenv import load_dotenv
from routine_data import combined_routine, subject_map, type_map
from discord.ext.commands import has_role

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_C_ROLE_ID = int(os.getenv("GROUP_C_ROLE_ID"))
GROUP_D_ROLE_ID = int(os.getenv("GROUP_D_ROLE_ID"))
CLASS_ROLE_ID = int(os.getenv("CLASS_ROLE_ID"))
CR_ROLE_ID = int(os.getenv("CR_ROLE_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
notified_classes = set()
cancelled_classes = set()

def parse_time_range(time_range):
    return datetime.strptime(time_range.split(" - ")[0], "%H:%M").time()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await asyncio.sleep(1)
    check_schedule.start()

@bot.command()
async def test(ctx):
    await ctx.send("✅ Bot is working!")

class CancelClassView(View):
    def __init__(self, classes_today):
        super().__init__(timeout=60)
        self.add_item(CancelClassSelect(classes_today))

class CancelClassSelect(Select):
    def __init__(self, classes_today):
        options = []
        now = datetime.now()
        today_str = now.strftime("%A")

        for c in classes_today:
            time = c['time']
            entry_start_time = parse_time_range(time)
            class_datetime = datetime.combine(now.date(), entry_start_time)

            if class_datetime < now:
                continue

            if isinstance(c['subject'], dict):
                for group in ('C', 'D'):
                    subject = c['subject'].get(group)
                    type_ = c['type'].get(group)
                    if not subject or subject == "BREAK":
                        continue
                    if (today_str, time, group) in cancelled_classes:
                        continue
                    type_name = type_map.get(type_, "Lecture")
                    subject_name = subject_map.get(subject, subject)
                    label = f"{type_name}: {subject_name} ({group}) at {time}"
                    value = f"{group}|{time}"
                    options.append(discord.SelectOption(label=label, value=value))
            else:
                subject = c['subject']
                if subject == "BREAK":
                    continue
                if (today_str, time, "BOTH") in cancelled_classes:
                    continue
                type_ = type_map.get(c.get('type'), "Lecture")
                subject_name = subject_map.get(subject, subject)
                label = f"{type_}: {subject_name} at {time}"
                value = f"BOTH|{time}"
                options.append(discord.SelectOption(label=label, value=value))

        super().__init__(
            placeholder="Select a class to cancel...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        # --- ROLE CHECK ---
        if CR_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(
                "🚫 You are not authorized to cancel classes.",
                ephemeral=True
            )
            return

        value = self.values[0]
        group, time = value.split("|")
        today = datetime.now().strftime("%A")
        cancelled_classes.add((today, time, group))

        if group == "BOTH":
            role_ping = f"<@&{CLASS_ROLE_ID}>"
            routine_entry = next(e for e in combined_routine[today] if e['time'] == time)
            subject = routine_entry['subject']
            type_ = type_map.get(routine_entry.get('type'), "Lecture")
            subject_name = subject_map.get(subject, subject)
        else:
            role_ping = f"<@&{GROUP_C_ROLE_ID}>" if group == "C" else f"<@&{GROUP_D_ROLE_ID}>"
            routine_entry = next(e for e in combined_routine[today] if e['time'] == time)
            subject = routine_entry['subject'].get(group)
            type_ = type_map.get(routine_entry['type'].get(group), "Lecture")
            subject_name = subject_map.get(subject, subject)

        await interaction.response.send_message(
            f"🚫 {role_ping} **{type_} canceled!**\n📚 {subject_name} at {time} will not be held today.",
            allowed_mentions=discord.AllowedMentions(roles=True)
        )


@bot.command()
async def cancelclass(ctx):
    if CR_ROLE_ID not in [role.id for role in ctx.author.roles]:
        await ctx.send("🚫 You are not authorized to cancel classes.")
        return

    today = datetime.now().strftime("%A")
    classes_today = [entry for entry in combined_routine.get(today, []) if "BREAK" not in str(entry['subject'])]

    if not classes_today:
        await ctx.send("No classes scheduled today.")
        return

    await ctx.send("Select the class to cancel:", view=CancelClassView(classes_today))

@bot.command()
async def classes(ctx):
    now = datetime.now()
    today = now.strftime("%A")
    user_roles = [role.id for role in ctx.author.roles]

    if GROUP_C_ROLE_ID in user_roles:
        user_group = "C"
    elif GROUP_D_ROLE_ID in user_roles:
        user_group = "D"
    else:
        user_group = "BOTH"

    schedule = combined_routine.get(today, [])
    remaining_classes = []

    for entry in schedule:
        entry_start_time = parse_time_range(entry['time'])
        class_datetime = datetime.combine(now.date(), entry_start_time)

        if class_datetime < now:
            continue

        if isinstance(entry['subject'], dict):
            if user_group == "BOTH":
                if all((today, entry['time'], group) in cancelled_classes for group in ('C', 'D')):
                    continue
            else:
                if (today, entry['time'], user_group) in cancelled_classes:
                    continue
        else:
            if (today, entry['time'], "BOTH") in cancelled_classes:
                continue

        if isinstance(entry['subject'], dict):
            if all(subj == "BREAK" for subj in entry['subject'].values()):
                continue
        else:
            if entry['subject'] == "BREAK":
                continue

        if user_group == "BOTH":
            if isinstance(entry['subject'], dict):
                for group in ('C', 'D'):
                    subject = entry['subject'].get(group)
                    if subject == "BREAK" or not subject:
                        continue
                    if (today, entry['time'], group) in cancelled_classes:
                        continue
                    type_ = type_map.get(entry['type'].get(group), "Lecture")
                    subject_name = subject_map.get(subject, subject)
                    remaining_classes.append(f"({group}) {type_}: {subject_name} at {entry['time']}")
            else:
                subject = entry['subject']
                type_ = type_map.get(entry.get('type'), "Lecture")
                subject_name = subject_map.get(subject, subject)
                remaining_classes.append(f"{type_}: {subject_name} at {entry['time']}")
        else:
            if isinstance(entry['subject'], dict):
                subject = entry['subject'].get(user_group)
                if not subject or subject == "BREAK":
                    continue
                if (today, entry['time'], user_group) in cancelled_classes:
                    continue
                type_ = type_map.get(entry['type'].get(user_group), "Lecture")
                subject_name = subject_map.get(subject, subject)
                remaining_classes.append(f"{type_}: {subject_name} at {entry['time']}")
            else:
                subject = entry['subject']
                if subject == "BREAK":
                    continue
                if (today, entry['time'], "BOTH") in cancelled_classes:
                    continue
                type_ = type_map.get(entry.get('type'), "Lecture")
                subject_name = subject_map.get(subject, subject)
                remaining_classes.append(f"{type_}: {subject_name} at {entry['time']}")

    if not remaining_classes:
        await ctx.send("✅ No remaining classes for today!")
        return

    title = f"📅 Remaining classes for {'Group ' + user_group if user_group != 'BOTH' else 'All Groups'} today:"
    message = "\n".join(remaining_classes)
    await ctx.send(f"{title}\n{message}")

@bot.command()
async def tomorrow(ctx):
    now = datetime.now()
    tomorrow_date = now + timedelta(days=1)
    tomorrow_day = tomorrow_date.strftime("%A")

    user_roles = [role.id for role in ctx.author.roles]
    if GROUP_C_ROLE_ID in user_roles:
        user_group = "C"
    elif GROUP_D_ROLE_ID in user_roles:
        user_group = "D"
    else:
        user_group = "BOTH"

    schedule = combined_routine.get(tomorrow_day, [])
    if not schedule:
        await ctx.send(f"📅 No classes scheduled for tomorrow ({tomorrow_day}).")
        return

    classes_list = []
    for entry in schedule:
        if isinstance(entry['subject'], dict):
            if user_group == "BOTH":
                for group in ('C', 'D'):
                    subject = entry['subject'].get(group)
                    if not subject or subject == "BREAK":
                        continue
                    type_ = type_map.get(entry['type'].get(group), "Lecture")
                    subject_name = subject_map.get(subject, subject)
                    classes_list.append(f"({group}) {type_}: {subject_name} at {entry['time']}")
            else:
                subject = entry['subject'].get(user_group)
                if not subject or subject == "BREAK":
                    continue
                type_ = type_map.get(entry['type'].get(user_group), "Lecture")
                subject_name = subject_map.get(subject, subject)
                classes_list.append(f"{type_}: {subject_name} at {entry['time']}")
        else:
            subject = entry['subject']
            if subject == "BREAK":
                continue
            type_ = type_map.get(entry.get('type'), "Lecture")
            subject_name = subject_map.get(subject, subject)
            classes_list.append(f"{type_}: {subject_name} at {entry['time']}")

    if not classes_list:
        await ctx.send(f"✅ No classes for you tomorrow ({tomorrow_day})!")
        return

    message = f"📅 Classes for tomorrow ({tomorrow_day}):\n" + "\n".join(classes_list)
    await ctx.send(message)

@bot.command()
async def week(ctx):
    user_roles = [role.id for role in ctx.author.roles]
    if GROUP_C_ROLE_ID in user_roles:
        user_group = "C"
    elif GROUP_D_ROLE_ID in user_roles:
        user_group = "D"
    else:
        user_group = "BOTH"

    messages = []
    for day in ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]:
        schedule = combined_routine.get(day, [])
        day_classes = []

        for entry in schedule:
            if isinstance(entry['subject'], dict):
                if user_group == "BOTH":
                    for group in ('C', 'D'):
                        subject = entry['subject'].get(group)
                        if not subject or subject == "BREAK":
                            continue
                        type_ = type_map.get(entry['type'].get(group), "Lecture")
                        subject_name = subject_map.get(subject, subject)
                        day_classes.append(f"({group}) {type_}: {subject_name} at {entry['time']}")
                else:
                    subject = entry['subject'].get(user_group)
                    if not subject or subject == "BREAK":
                        continue
                    type_ = type_map.get(entry['type'].get(user_group), "Lecture")
                    subject_name = subject_map.get(subject, subject)
                    day_classes.append(f"{type_}: {subject_name} at {entry['time']}")
            else:
                subject = entry['subject']
                if subject == "BREAK":
                    continue
                type_ = type_map.get(entry.get('type'), "Lecture")
                subject_name = subject_map.get(subject, subject)
                day_classes.append(f"{type_}: {subject_name} at {entry['time']}")

        if day_classes:
            day_message = f"**{day}:**\n" + "\n".join(day_classes)
            messages.append(day_message)

    if not messages:
        await ctx.send("❌ No classes scheduled this week.")
        return

    await ctx.send("📅 **Weekly Schedule:**\n" + "\n\n".join(messages))

@bot.command()
@has_role(CR_ROLE_ID)
async def resetcancellations(ctx):
    cancelled_classes.clear()
    notified_classes.clear()
    await ctx.send("✅ All class cancellations and notifications have been reset.")

@tasks.loop(minutes=1)
async def check_schedule():
    global notified_classes
    try:
        now = datetime.now()
        today = now.strftime("%A")
        notified_classes = {entry for entry in notified_classes if entry[0] == today}

        for entry in combined_routine.get(today, []):
            entry_start_time = parse_time_range(entry['time'])
            class_datetime = datetime.combine(now.date(), entry_start_time)
            # reminder_datetime = class_datetime - timedelta(minutes=15)
            reminder_datetime = now

            if abs((now - reminder_datetime).total_seconds()) <= 60:
                if isinstance(entry['subject'], dict):
                    for group in ('C', 'D'):
                        subject = entry['subject'].get(group)
                        if not subject or subject == "BREAK":
                            continue
                        type_ = type_map.get(entry['type'].get(group), "Lecture")
                        subject_name = subject_map.get(subject, subject)
                        notification_key = (today, entry['time'], group)
                        if notification_key in notified_classes or notification_key in cancelled_classes:
                            continue
                        role = f"<@&{GROUP_C_ROLE_ID}>" if group == "C" else f"<@&{GROUP_D_ROLE_ID}>"
                        msg = f"{role} ⏰ **Upcoming {type_} in 15 minutes!**\n📚 {subject_name} at {entry['time']}"
                        await bot.get_channel(CHANNEL_ID).send(msg)
                        notified_classes.add(notification_key)
                else:
                    subject = entry['subject']
                    if subject == "BREAK":
                        continue
                    type_ = type_map.get(entry.get('type'), "Lecture")
                    subject_name = subject_map.get(subject, subject)
                    notification_key = (today, entry['time'], "BOTH")
                    if notification_key in notified_classes or notification_key in cancelled_classes:
                        continue
                    role = f"<@&{CLASS_ROLE_ID}>"
                    msg = f"{role} ⏰ **Upcoming {type_} in 15 minutes!**\n📚 {subject_name} at {entry['time']}"
                    await bot.get_channel(CHANNEL_ID).send(msg)
                    notified_classes.add(notification_key)
    except Exception as e:
        print(f"Error in check_schedule: {e}")

bot.run(TOKEN)
