import os
import json
import discord
from discord import app_commands, Interaction
from discord.ext import commands


# Charger le token

TOKEN = os.getenv("DISCORD_TOKEN_AVANCEMENT")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN non défini dans Railway")
    
import discord
from discord import app_commands
from discord.ext import commands
import os

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise ValueError("DISCORD_TOKEN non défini dans Railway")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ====== BASE DE DONNÉES EN MÉMOIRE ======
series_db = {}  
profiles_db = {}  

# Structure series_db :
# {
#   "Nanomancer": {
#       "cover": "url",
#       "va": "url",
#       "salon": channel_id,
#       "roles": {"trad": user_id, "check": None, "clean": None, "edit": None, "qedit": None},
#       "progress": {"trad": 0, "check": 0, "clean": 0, "edit": 0, "qedit": 0}
#   }
# }

# ====== EVENTS ======
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot connecté : {bot.user}")

# ====== /NEW_SERIE ======
@bot.tree.command(name="new_serie", description="Ajouter une nouvelle série")
async def new_serie(interaction: discord.Interaction, nom: str, cover: str, va: str, salon: discord.TextChannel):
    series_db[nom] = {
        "cover": cover,
        "va": va,
        "salon": salon.id,
        "roles": {"trad": None, "check": None, "clean": None, "edit": None, "qedit": None},
        "progress": {"trad": 0, "check": 0, "clean": 0, "edit": 0, "qedit": 0}
    }
    await interaction.response.send_message(f"Série **{nom}** ajoutée.")

# ====== /ASSIGNEMENT ======
@bot.tree.command(name="assignement", description="Assigner un rôle sur une série")
async def assignement(interaction: discord.Interaction, membre: discord.Member, role: str, serie: str):
    role = role.lower()

    if serie not in series_db:
        await interaction.response.send_message("Série inconnue.")
        return

    if role not in ["trad", "check", "clean", "edit", "qedit"]:
        await interaction.response.send_message("Rôle invalide.")
        return

    # Donner accès au salon
    salon = interaction.guild.get_channel(series_db[serie]["salon"])
    await salon.set_permissions(membre, read_messages=True, send_messages=True)

    # Donner rôle Discord
    discord_role = discord.utils.get(interaction.guild.roles, name=role)
    if discord_role:
        await membre.add_roles(discord_role)

    series_db[serie]["roles"][role] = membre.id

    # Profil utilisateur
    if membre.id not in profiles_db:
        profiles_db[membre.id] = {"roles": set(), "chapters": 0, "series": set()}
    profiles_db[membre.id]["roles"].add(role)
    profiles_db[membre.id]["series"].add(serie)

    await interaction.response.send_message(f"{membre.mention} est maintenant **{role}** sur **{serie}**.")

# ====== /INFOS ======
@bot.tree.command(name="infos", description="Voir infos d'une série")
async def infos(interaction: discord.Interaction, serie: str):
    if serie not in series_db:
        await interaction.response.send_message("Série inconnue.")
        return

    s = series_db[serie]

    msg = (
        f"**{serie}**\n"
        f"Cover : {s['cover']}\n"
        f"VA : {s['va']}\n\n"
        f"Trad : {mention_user(s['roles']['trad'])} ({s['progress']['trad']})\n"
        f"Check : {mention_user(s['roles']['check'])} ({s['progress']['check']})\n"
        f"Clean : {mention_user(s['roles']['clean'])} ({s['progress']['clean']})\n"
        f"Edit : {mention_user(s['roles']['edit'])} ({s['progress']['edit']})\n"
        f"QEdit : {mention_user(s['roles']['qedit'])} ({s['progress']['qedit']})\n"
    )

    await interaction.response.send_message(msg)

def mention_user(user_id):
    return f"<@{user_id}>" if user_id else "Non assigné"

# ====== /PROFIL ======
@bot.tree.command(name="profil", description="Voir profil d'un membre")
async def profil(interaction: discord.Interaction, membre: discord.Member):
    if membre.id not in profiles_db:
        await interaction.response.send_message("Aucune donnée.")
        return

    p = profiles_db[membre.id]
    roles = ", ".join(p["roles"])
    series = ", ".join(p["series"])

    msg = (
        f"Profil de {membre.mention}\n"
        f"Rôles : {roles}\n"
        f"Chapitres faits : {p['chapters']}\n"
        f"Séries : {series}"
    )
    await interaction.response.send_message(msg)

# ====== /HELP ======
@bot.tree.command(name="help", description="Voir les commandes")
async def help_cmd(interaction: discord.Interaction):
    msg = (
        "/new_serie\n"
        "/assignement\n"
        "/infos\n"
        "/profil\n"
        "/announce"
    )
    await interaction.response.send_message(msg)

# ====== /ANNOUNCE ======
@bot.tree.command(name="announce", description="Annoncer un nouveau chapitre")
async def announce(interaction: discord.Interaction, serie: str, lien: str):
    await interaction.response.send_message(f"@everyone **{serie}** nouveau chapitre !\n{lien}")

bot.run(TOKEN)
# Intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = commands.Bot(command_prefix="!", intents=intents)
tree = client.tree

# Fichier JSON partagé avec Bot 1
DATA_FILE = "data_avancement.json"

staff_roles = ["trad", "check", "clean", "edit", "qedit"]

# ---------------- UTILITAIRES ----------------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def next_role(role):
    idx = staff_roles.index(role.lower())
    next_idx = (idx + 1) % len(staff_roles)
    return staff_roles[next_idx]

def role_valid(role_name):
    return role_name.lower() in staff_roles

# ---------------- COMMANDES ----------------
@tree.command(name="avancement", description="Valider un chapitre pour un rôle sur une série")
@app_commands.describe(role="Rôle du staff", serie="Salon textuel de la série")
async def avancement(interaction: Interaction, role: str, serie: discord.TextChannel):
    role_lower = role.lower()
    if not role_valid(role_lower):
        await interaction.response.send_message(f"Rôle invalide. Choisis parmi : {', '.join(staff_roles)}.", ephemeral=True)
        return

    user = interaction.user
    data = load_data()
    serie_name = serie.name
    if serie_name not in data:
        await interaction.response.send_message(f"La série **{serie_name}** n'existe pas.", ephemeral=True)
        return

    serie_data = data[serie_name]
    member_id = serie_data.get("members", {}).get(role_lower)
    if member_id != user.id:
        await interaction.response.send_message(f"Tu n'as pas le rôle **{role_lower.capitalize()}** pour **{serie_name}**.", ephemeral=True)
        return

    # Récupérer chapitre actuel
    chap = serie_data.get("current_chap", 1)

    # Enregistrer le chapitre pour ce rôle
    serie_data.setdefault("chapters", {}).setdefault(str(chap), {})
    serie_data["chapters"][str(chap)][role_lower] = user.id

    # Déterminer rôle suivant
    next_r = next_role(role_lower)
    next_member_id = serie_data.get("members", {}).get(next_r)
    next_member_mention = f"<@{next_member_id}>" if next_member_id else "Pas encore assigné"

    save_data(data)

    await interaction.response.send_message(
        f"Chapitre {chap} de **{serie_name}** validé en **{role_lower.capitalize()}**, {next_member_mention} à toi de jouer !"
    )

    # Si tous les rôles ont validé, passer au chapitre suivant
    chap_data = serie_data["chapters"][str(chap)]
    if all(r in chap_data for r in staff_roles):
        serie_data["current_chap"] = chap + 1
        save_data(data)
        await interaction.followup.send(f"Tous les rôles ont validé le chapitre {chap}. Chapitre suivant : {chap + 1} !")

# ---------------- EVENTS ----------------
@client.event
async def on_ready():
    await tree.sync()
    print(f"Bot Avancement connecté en tant que {client.user}")

client.run(TOKEN)

