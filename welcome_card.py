import io
from PIL import Image, ImageDraw, ImageFont

def generate_welcome_card(avatar_bytes: bytes, member_name: str = "", guild_name: str = "BVNekoo") -> io.BytesIO:
    """Génère la carte de bienvenue horizontale au format exact de DraftBot (Screen 2)."""
    # Supersampling 2x (1400x480 réduit à 700x240) pour une netteté absolue
    w2, h2 = 1400, 480
    img = Image.new("RGBA", (w2, h2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fond rectangulaire arrondi style Discord (#2b2d31)
    card_color = (43, 45, 49)
    draw.rounded_rectangle((0, 0, w2, h2), radius=36, fill=card_color)

    # Avatar circulaire à gauche
    avatar_size2 = 270
    avatar_x2 = 90
    avatar_y2 = (h2 - avatar_size2) // 2

    try:
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    except Exception:
        avatar = Image.new("RGBA", (avatar_size2, avatar_size2), (88, 101, 242))

    avatar = avatar.resize((avatar_size2, avatar_size2), Image.Resampling.LANCZOS)
    mask = Image.new("L", (avatar_size2 * 2, avatar_size2 * 2), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avatar_size2 * 2, avatar_size2 * 2), fill=255)
    mask = mask.resize((avatar_size2, avatar_size2), Image.Resampling.LANCZOS)

    circular_avatar = Image.new("RGBA", (avatar_size2, avatar_size2), (0, 0, 0, 0))
    circular_avatar.paste(avatar, (0, 0), mask=mask)
    img.paste(circular_avatar, (avatar_x2, avatar_y2), mask=circular_avatar)

    # Textes à droite
    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 96)
        font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 44)
        font_guild = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 86)
    except Exception:
        try:
            font_title = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 96)
            font_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 44)
            font_guild = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 86)
        except Exception:
            font_title = font_sub = font_guild = ImageFont.load_default()

    text_x = 410
    # Bienvenue
    draw.text((text_x, 75), "Bienvenue", fill=(255, 255, 255), font=font_title)
    # sur le serveur Discord
    draw.text((text_x, 200), "sur le serveur Discord", fill=(219, 222, 225), font=font_sub)
    # Nom du serveur (ex: BVNekoo)
    display_guild = guild_name if guild_name and guild_name != "BV" else "BVNekoo"
    draw.text((text_x, 265), display_guild, fill=(255, 255, 255), font=font_guild)

    # Réduction à 700x240 avec Lanczos
    final_img = img.resize((700, 240), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    final_img.save(output, format="PNG")
    output.seek(0)
    return output
