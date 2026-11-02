import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import uvicorn
import config
from crypto_utils import create_verification_token
import database
from web_server import app as fastapi_app, set_discord_bot
from welcome_card import generate_welcome_card

import sys
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Intents Discord (SERVER MEMBERS INTENT activé pour détecter les arrivées et attribuer l'auto-rôle)
intents = discord.Intents.default()
intents.members = True

class FollowerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Initialise la base de données SQLite
        database.init_db()
        print("📁 Base de données SQLite initialisée.")

        # Lie le bot au serveur web FastAPI
        set_discord_bot(self)

        # Synchronise instantanément les commandes slash sur le serveur spécifique
        try:
            if config.DISCORD_GUILD_ID:
                guild_obj = discord.Object(id=config.DISCORD_GUILD_ID)
                self.tree.copy_global_to(guild=guild_obj)
                synced = await self.tree.sync(guild=guild_obj)
                print(f"⚡ Slash commands synchronisées INSTANTANÉMENT pour ton serveur ({len(synced)} commandes).")
            else:
                synced = await self.tree.sync()
                print(f"⚡ Slash commands synchronisées globalement ({len(synced)} commandes).")
        except Exception as e:
            print(f"⚠️ Erreur lors de la synchronisation des commandes : {e}")

bot = FollowerBot()

# Vue avec bouton cliquable pour obtenir son lien de vérification
class VerifyButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟣 Récupérer mon rôle Follower Twitch", style=discord.ButtonStyle.primary, custom_id="persistent_verify_btn")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        token = create_verification_token(interaction.user.id)
        verify_url = f"{config.BASE_URL}/verify?token={token}"

        embed = discord.Embed(
            title="🟣 Rôle Follower Twitch",
            description=(
                f"Bonjour {interaction.user.mention} !\n\n"
                f"Clique sur le lien ci-dessous pour lier ton compte Twitch et recevoir automatiquement le rôle **> Follower Twitch** :\n\n"
                f"👉 [**Clique ici pour lier ton Twitch**]({verify_url})\n\n"
                f"*Ce lien t'est personnel et expire dans 1 heure.*"
            ),
            color=0x9146FF
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    # Enregistrer la vue persistante pour qu'elle continue de marcher après un redémarrage
    bot.add_view(VerifyButtonView())
    print(f" Connecté en tant que {bot.user} (ID: {bot.user.id})")
    print(f" Serveur web actif sur : {config.BASE_URL}")

# Commande slash /verifier (visible uniquement par la personne qui la tape)
@bot.tree.command(name="verifier", description="Reçois ton lien personnel pour lier ton compte Twitch et obtenir ton rôle.")
async def verifier(interaction: discord.Interaction):
    token = create_verification_token(interaction.user.id)
    verify_url = f"{config.BASE_URL}/verify?token={token}"

    embed = discord.Embed(
        title="🟣 Rôle Follower Twitch",
        description=(
            f"Bonjour {interaction.user.mention} !\n\n"
            f"Clique sur le lien ci-dessous pour lier ton compte Twitch et recevoir ton rôle :\n\n"
            f"👉 [**Accéder à la vérification Twitch**]({verify_url})\n\n"
            f"*Ce lien t'est personnel et expire dans 1 heure.*"
        ),
        color=0x9146FF
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Commande slash /setup_panel (Pour installer le panneau dans un salon)
@bot.tree.command(name="setup_panel", description="Affiche le message permanent avec bouton pour le rôle Follower Twitch.")
@app_commands.default_permissions(administrator=True)
async def setup_panel(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🎁 Récupère ton rôle Follower Twitch !",
        description=(
            "Tu me suis sur Twitch (**bvnekoo**) ?\n\n"
            "Clique sur le bouton ci-dessous pour lier ton compte Twitch et débloquer automatiquement le rôle **> Follower Twitch** !"
        ),
        color=0x9146FF
    )
    embed.set_footer(text="Système de vérification Twitch automatique")
    await interaction.channel.send(embed=embed, view=VerifyButtonView())
    await interaction.response.send_message("✅ Panneau Follower Twitch installé avec succès !", ephemeral=True)

# Fonction pour envoyer le message de bienvenue dans tous les salons configurés
async def send_welcome_to_channels(guild: discord.Guild, member: discord.Member | discord.User):
    if not config.WELCOME_CHANNEL_IDS:
        return
    
    avatar_bytes = await member.display_avatar.read()

    # Récupérer la bannière Discord du membre si elle existe
    banner_bytes = None
    try:
        user_full = await bot.fetch_user(member.id)
        if user_full.banner:
            banner_bytes = await user_full.banner.read()
    except Exception:
        banner_bytes = None

    for ch_id in config.WELCOME_CHANNEL_IDS:
        channel = guild.get_channel(ch_id)
        if not channel:
            continue
        try:
            card_buffer = generate_welcome_card(avatar_bytes, banner_bytes, member.display_name, guild.name)
            file = discord.File(fp=card_buffer, filename="welcome.png")

            embed = discord.Embed(
                title="Bienvenue sur le discord !",
                description=member.mention,
                color=0x5865F2
            )
            embed.set_image(url="attachment://welcome.png")
            await channel.send(embed=embed, file=file)
        except Exception as e:
            print(f"⚠️ Erreur lors de l'envoi du message dans le salon {ch_id} : {e}")

# Événement de Bienvenue & Auto-rôle (Remplace DraftBot)
@bot.event
async def on_member_join(member: discord.Member):
    # 1. Attribuer automatiquement le rôle de membre (ex: 👥ゝMembre)
    if config.AUTO_JOIN_ROLE_ID:
        role = member.guild.get_role(config.AUTO_JOIN_ROLE_ID)
        if role:
            try:
                await member.add_roles(role, reason="Auto-rôle automatique à l'arrivée")
                print(f"✅ Auto-rôle {role.name} attribué à {member.name}")
            except Exception as e:
                print(f"⚠️ Erreur auto-rôle pour {member.name} : {e}")

    # 2. Envoyer le message de bienvenue avec l'avatar cerclé dans les salons
    await send_welcome_to_channels(member.guild, member)

# Commande slash /test_bienvenue pour tester le rendu immédiatement
@bot.tree.command(name="test_bienvenue", description="Envoie un exemple de message de bienvenue dans les salons configurés.")
@app_commands.default_permissions(administrator=True)
async def test_bienvenue(interaction: discord.Interaction):
    if not config.WELCOME_CHANNEL_IDS:
        await interaction.response.send_message("❌ Aucun salon de bienvenue configuré dans le fichier .env.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    try:
        await send_welcome_to_channels(interaction.guild, interaction.user)
        channels_mentions = " ".join([f"<#{cid}>" for cid in config.WELCOME_CHANNEL_IDS])
        await interaction.followup.send(f"✅ Message de bienvenue envoyé avec succès dans {channels_mentions} !", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Erreur lors de l'envoi : {e}", ephemeral=True)

# Commande classique !test_bienvenue (en texte direct sans slash)
@bot.command(name="test_bienvenue")
@commands.has_permissions(administrator=True)
async def cmd_test_bienvenue(ctx):
    if not config.WELCOME_CHANNEL_IDS:
        await ctx.send("❌ Aucun salon de bienvenue configuré dans le fichier .env.")
        return

    try:
        await send_welcome_to_channels(ctx.guild, ctx.author)
        await ctx.message.delete()
    except Exception as e:
        await ctx.send(f"❌ Erreur : {e}")

# Commande classique !setup_panel (en texte direct sans slash)
@bot.command(name="setup_panel")
@commands.has_permissions(administrator=True)
async def cmd_setup_panel(ctx):
    embed = discord.Embed(
        title="🎁 Récupère ton rôle Follower Twitch !",
        description=(
            "Tu me suis sur Twitch (**bvnekoo**) ?\n\n"
            "Clique sur le bouton ci-dessous pour lier ton compte Twitch et débloquer automatiquement le rôle **> Follower Twitch** !"
        ),
        color=0x9146FF
    )
    embed.set_footer(text="Système de vérification Twitch automatique")
    await ctx.channel.send(embed=embed, view=VerifyButtonView())
    await ctx.message.delete()

async def main():
    if not config.DISCORD_TOKEN:
        print("❌ ERREUR : Aucun DISCORD_TOKEN n'est défini dans le fichier .env !")
        print("Ajoute ton token dans le fichier .env puis relance le bot.")
        return

    # Configuration du serveur web uvicorn
    uvicorn_config = uvicorn.Config(
        app=fastapi_app,
        host="0.0.0.0",
        port=config.PORT,
        log_level="warning"
    )
    server = uvicorn.Server(uvicorn_config)

    # Lancement simultané du bot Discord et du serveur Web
    await asyncio.gather(
        bot.start(config.DISCORD_TOKEN),
        server.serve()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n Arrêt du bot.")
