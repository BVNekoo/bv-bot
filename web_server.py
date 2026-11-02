import os
import aiohttp
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import config
from crypto_utils import verify_token, create_verification_token
import database

app = FastAPI(title="Discord Follower Verifier")

# Route de santé pour Render
@app.get("/")
async def root():
    return {"status": "ok", "message": "BV Follower Bot is running!"}

# Stocke la référence au bot Discord pour pouvoir attribuer les rôles en direct
discord_bot = None

def set_discord_bot(bot_instance):
    global discord_bot
    discord_bot = bot_instance

async def grant_role_to_member(discord_id: int, role_id: int) -> tuple[bool, str]:
    """Attribue un rôle au membre Discord donné."""
    if not discord_bot:
        return False, "Bot Discord non connecté."
    if not role_id or role_id == 0:
        return False, "ID de rôle non configuré dans .env."

    guild = discord_bot.get_guild(config.DISCORD_GUILD_ID)
    if not guild:
        # Essayer de fetch la guild si pas en cache
        try:
            guild = await discord_bot.fetch_guild(config.DISCORD_GUILD_ID)
        except Exception:
            return False, f"Impossible de trouver le serveur Discord (ID: {config.DISCORD_GUILD_ID})."

    try:
        member = guild.get_member(discord_id)
        if not member:
            member = await guild.fetch_member(discord_id)
    except Exception:
        return False, f"Membre introuvable sur le serveur Discord (ID: {discord_id})."

    role = guild.get_role(role_id)
    if not role:
        return False, f"Rôle introuvable sur Discord (ID: {role_id})."

    try:
        await member.add_roles(role, reason="Follow vérifié automatiquement")
        return True, f"Rôle @{role.name} attribué avec succès !"
    except Exception as e:
        return False, f"Erreur de permission Discord : {e}"

# Page d'accueil / portail de vérification
@app.get("/verify", response_class=HTMLResponse)
async def verify_page(token: str):
    discord_id = verify_token(token)
    if not discord_id:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Lien Expiré</title>
            <style>
                body { background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
                .card { background: #1e293b; padding: 2rem; border-radius: 12px; text-align: center; max-width: 400px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
                h1 { color: #ef4444; }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>❌ Lien Expiré ou Invalide</h1>
                <p>Ce lien de vérification a expiré ou est incorrect.</p>
                <p>Retourne sur Discord et tape la commande <code>/verifier</code> pour en obtenir un nouveau.</p>
            </div>
        </body>
        </html>
        """, status_code=400)

    # Récupérer l'état actuel de l'utilisateur
    user_data = database.get_user_by_discord_id(str(discord_id))
    twitch_done = bool(user_data and user_data["twitch_id"])
    youtube_done = bool(user_data and user_data["youtube_channel_id"])
    kick_done = bool(user_data and user_data["kick_username"])

    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Vérification des Follows</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                background: #0f172a;
                color: #f8fafc;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                padding: 1rem;
            }}
            .container {{
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 16px;
                padding: 2.5rem;
                max-width: 480px;
                width: 100%;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            }}
            h1 {{
                font-size: 1.5rem;
                text-align: center;
                margin-bottom: 0.5rem;
                color: #5865F2;
            }}
            p.subtitle {{
                text-align: center;
                color: #94a3b8;
                font-size: 0.9rem;
                margin-bottom: 2rem;
            }}
            .platform-card {{
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 1.25rem;
                margin-bottom: 1.25rem;
                display: flex;
                flex-direction: column;
                gap: 0.75rem;
            }}
            .platform-header {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                font-weight: 600;
            }}
            .badge-done {{
                background: #059669;
                color: #ecfdf5;
                font-size: 0.75rem;
                padding: 0.2rem 0.6rem;
                border-radius: 9999px;
            }}
            .btn {{
                display: inline-block;
                text-align: center;
                text-decoration: none;
                padding: 0.75rem 1rem;
                border-radius: 8px;
                font-weight: 600;
                font-size: 0.95rem;
                cursor: pointer;
                transition: opacity 0.2s;
                border: none;
                width: 100%;
            }}
            .btn:hover {{ opacity: 0.9; }}
            .btn-twitch {{ background: #9146FF; color: white; }}
            .btn-youtube {{ background: #FF0000; color: white; }}
            .btn-kick {{ background: #53FC18; color: black; }}
            .input-kick {{
                background: #1e293b;
                border: 1px solid #475569;
                color: white;
                padding: 0.6rem 0.8rem;
                border-radius: 6px;
                width: 100%;
                margin-bottom: 0.5rem;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🟣 Rôle Follower Twitch</h1>
            <p class="subtitle">Connecte ton compte Twitch pour vérifier ton follow sur la chaîne <b>bvnekoo</b> et recevoir ton rôle Discord !</p>

            <!-- Twitch -->
            <div class="platform-card">
                <div class="platform-header">
                    <span>Twitch (@bvnekoo)</span>
                    {"<span class='badge-done'>✅ Rôle Obtenu</span>" if twitch_done else ""}
                </div>
                {"<p style='color:#10b981; font-size:0.95rem; text-align:center; padding: 0.5rem;'>Ton rôle <b>> Follower Twitch</b> est déjà actif sur le serveur !</p>" if twitch_done else f"<a href='/auth/twitch/start?token={token}' class='btn btn-twitch'>Se connecter avec Twitch</a>"}
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


# --- TWITCH OAUTH2 ---
@app.get("/auth/twitch/start")
async def twitch_start(token: str):
    discord_id = verify_token(token)
    if not discord_id:
        raise HTTPException(status_code=400, detail="Token invalide")
    
    redirect_uri = f"{config.BASE_URL}/auth/twitch/callback"
    scopes = "user:read:follows"
    url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={config.TWITCH_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scopes}"
        f"&state={token}"
    )
    return RedirectResponse(url=url)

@app.get("/auth/twitch/callback", response_class=HTMLResponse)
async def twitch_callback(code: str, state: str):
    discord_id = verify_token(state)
    if not discord_id:
        return HTMLResponse("Token de session invalide.", status_code=400)

    # 1. Échanger le code contre un token d'accès Twitch
    redirect_uri = f"{config.BASE_URL}/auth/twitch/callback"
    async with aiohttp.ClientSession() as session:
        token_url = "https://id.twitch.tv/oauth2/token"
        params = {
            "client_id": config.TWITCH_CLIENT_ID,
            "client_secret": config.TWITCH_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        async with session.post(token_url, data=params) as resp:
            data = await resp.json()
            access_token = data.get("access_token")
            if not access_token:
                return HTMLResponse(f"Erreur d'authentification Twitch : {data.get('message', 'inconnue')}", status_code=400)

        # 2. Obtenir l'ID Twitch de l'utilisateur
        headers = {
            "Client-ID": config.TWITCH_CLIENT_ID,
            "Authorization": f"Bearer {access_token}"
        }
        async with session.get("https://api.twitch.tv/helix/users", headers=headers) as resp:
            user_data = await resp.json()
            if "data" not in user_data or not user_data["data"]:
                return HTMLResponse("Impossible de récupérer ton compte Twitch.", status_code=400)
            user_info = user_data["data"][0]
            twitch_user_id = user_info["id"]
            twitch_login = user_info["login"]

        # 3. Vérifier s'il suit le diffuseur (broadcaster)
        follow_url = f"https://api.twitch.tv/helix/channels/followed?user_id={twitch_user_id}&broadcaster_id={config.TWITCH_BROADCASTER_ID}"
        async with session.get(follow_url, headers=headers) as resp:
            follow_data = await resp.json()
            is_following = bool(follow_data.get("data") and len(follow_data["data"]) > 0)

        # Si l'utilisateur est le streamer lui-même (bvnekoo), il a évidemment le rôle d'office !
        if str(twitch_user_id) == str(config.TWITCH_BROADCASTER_ID):
            is_following = True

    if not is_following:
        return HTMLResponse(f"""
        <div style="font-family: sans-serif; text-align: center; padding: 3rem; background: #0f172a; color: white; min-height: 100vh;">
            <h1 style="color: #ef4444;">❌ Tu ne suis pas encore la chaîne Twitch !</h1>
            <p>Le compte <b>{twitch_login}</b> n'est pas abonné à la chaîne.</p>
            <p>Va follow la chaîne sur Twitch, puis réessaie !</p>
            <br>
            <a href="/verify?token={state}" style="color: #5865F2;">⬅️ Réessayer</a>
        </div>
        """)

    # 4. Attribuer le rôle Discord et sauvegarder en base
    database.save_twitch_link(str(discord_id), twitch_user_id, twitch_login)
    success, msg = await grant_role_to_member(discord_id, config.TWITCH_FOLLOWER_ROLE_ID)

    return HTMLResponse(f"""
    <div style="font-family: sans-serif; text-align: center; padding: 3rem; background: #0f172a; color: white; min-height: 100vh;">
        <h1 style="color: #10b981;">🎉 Bravo {twitch_login} !</h1>
        <p>Follow Twitch confirmé !</p>
        <p style="color: #94a3b8;">{msg}</p>
        <br>
        <a href="/verify?token={state}" style="color: #5865F2;">⬅️ Retourner à la liste des rôles</a>
    </div>
    """)


# --- YOUTUBE OAUTH2 ---
@app.get("/auth/youtube/start")
async def youtube_start(token: str):
    discord_id = verify_token(token)
    if not discord_id:
        raise HTTPException(status_code=400, detail="Token invalide")
    
    redirect_uri = f"{config.BASE_URL}/auth/youtube/callback"
    scopes = "https://www.googleapis.com/auth/youtube.readonly"
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={config.YOUTUBE_API_KEY}" # Sera remplacé par le Client ID Google OAuth
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scopes}"
        f"&state={token}"
        f"&access_type=offline"
    )
    return RedirectResponse(url=url)

@app.get("/auth/youtube/callback", response_class=HTMLResponse)
async def youtube_callback(code: str, state: str):
    discord_id = verify_token(state)
    if not discord_id:
        return HTMLResponse("Token de session invalide.", status_code=400)

    # Note: On implémentera l'échange OAuth Google à l'étape 3
    return HTMLResponse("""
    <div style="font-family: sans-serif; text-align: center; padding: 3rem; background: #0f172a; color: white; min-height: 100vh;">
        <h1 style="color: #3b82f6;">Configuration YouTube en cours</h1>
        <p>L'intégration YouTube sera finalisée dès l'étape 3.</p>
    </div>
    """)


# --- KICK VERIFICATION ---
@app.post("/auth/kick/verify", response_class=HTMLResponse)
async def kick_verify(request: Request):
    form = await request.form()
    token = form.get("token", "")
    kick_username = form.get("kick_username", "").strip()

    discord_id = verify_token(token)
    if not discord_id:
        return HTMLResponse("Token de session invalide.", status_code=400)

    if not kick_username:
        return HTMLResponse("Veuillez indiquer un pseudo Kick valide.", status_code=400)

    # Vérification via l'API Kick
    # Pour l'étape 4, on sauvegarde et teste l'API
    database.save_kick_link(str(discord_id), kick_username)
    success, msg = await grant_role_to_member(discord_id, config.KICK_FOLLOWER_ROLE_ID)

    return HTMLResponse(f"""
    <div style="font-family: sans-serif; text-align: center; padding: 3rem; background: #0f172a; color: white; min-height: 100vh;">
        <h1 style="color: #10b981;">✅ Pseudo Kick enregistré ({kick_username}) !</h1>
        <p style="color: #94a3b8;">{msg}</p>
        <br>
        <a href="/verify?token={token}" style="color: #5865F2;">⬅️ Retourner à la liste</a>
    </div>
    """)
