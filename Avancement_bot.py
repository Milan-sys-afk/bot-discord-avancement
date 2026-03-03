import discord
from discord import app_commands
from discord.ext import commands
import os
import json

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN non défini dans Railway")

GUILD_ID = int(os.getenv("GUILD_ID"))  # ID de ton serveur

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "avancement_data.json"

ROLES_ORDER = ["Trad", "Check", "Clean", "Edit", "Qedit"]


def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print("Bot Avancement connecté et commandes sync")


@app_commands.command(name="avancement", description="Valider l'avancement d'un chapitre")
@app_commands.describe(role="Rôle qui valide", salon="Salon de la série")
@app_commands.choices(role=[
    app_commands.Choice(name="Trad", value="Trad"),
    app_commands.Choice(name="Check", value="Check"),
    app_commands.Choice(name="Clean", value="Clean"),
    app_commands.Choice(name="Edit", value="Edit"),
    app_commands.Choice(name="Qedit", value="Qedit"),
])
async def avancement(interaction: discord.Interaction, role: app_commands.Choice[str], salon: discord.TextChannel):

    user = interaction.user
    guild = interaction.guild

    role_name = role.value
    serie_name = salon.name

    member = guild.get_member(user.id)

    # Vérif rôle staff
    staff_role = discord.utils.get(guild.roles, name=role_name)
    if staff_role not in member.roles:
        await interaction.response.send_message(
            f"❌ Tu n'as pas le rôle {role_name}.",
            ephemeral=True
        )
        return

    # Vérif rôle série
    serie_role = discord.utils.get(guild.roles, name=serie_name)
    if serie_role not in member.roles:
        await interaction.response.send_message(
            f"❌ Tu n'es pas assigné à la série {serie_name}.",
            ephemeral=True
        )
        return

    data = load_data()

    if serie_name not in data:
        data[serie_name] = {
            "chapter": 0,
            "status": {}
        }

    current_chapter = data[serie_name]["chapter"] + 1
    data[serie_name]["chapter"] = current_chapter
    data[serie_name]["status"][role_name] = "validé"

    save_data(data)

    role_index = ROLES_ORDER.index(role_name)

    if role_index + 1 < len(ROLES_ORDER):
        next_role_name = ROLES_ORDER[role_index + 1]
        next_role = discord.utils.get(guild.roles, name=next_role_name)
        mention_next = next_role.mention if next_role else "@suivant"
    else:
        mention_next = "🎉 Chapitre terminé !"

    message = (
        f"📘 Chapitre {current_chapter} de {serie_name} validé en **{role_name}**, "
        f"{mention_next} à toi de jouer !"
    )

    await interaction.response.send_message(message)


bot.tree.add_command(avancement, guild=discord.Object(id=GUILD_ID))

bot.run(TOKEN)
