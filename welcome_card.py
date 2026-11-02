import io
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Chemins des polices intégrées au projet (fonctionnent sur Windows ET Linux/Render)
DIR_PATH = os.path.dirname(__file__)
FONT_BOLD_PATH = os.path.join(DIR_PATH, "font_bold.ttf")
FONT_REGULAR_PATH = os.path.join(DIR_PATH, "font_regular.ttf")

def generate_welcome_card(avatar_bytes: bytes, banner_bytes: bytes | None = None, member_name: str = "", guild_name: str = "BVNekoo") -> io.BytesIO:
    """Génère la bannière de bienvenue avec la bannière Discord du membre en fond."""
    w, h = 800, 270

    # 1. Fond : Bannière Discord du membre (ou avatar flouté en arrière-plan si pas de bannière)
    bg = None
    if banner_bytes:
        try:
            bg = Image.open(io.BytesIO(banner_bytes)).convert("RGBA")
            bg = bg.resize((w, h), Image.Resampling.LANCZOS)
        except Exception:
            bg = None

    if bg is None:
        try:
            bg = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            # Zoom et découpe pour remplir 800x270
            aspect = bg.width / bg.height
            new_h = int(w / aspect)
            if new_h < h:
                new_h = h
                new_w = int(h * aspect)
            else:
                new_w = w
            bg = bg.resize((new_w, new_h), Image.Resampling.LANCZOS)
            crop_top = (new_h - h) // 2
            bg = bg.crop((0, crop_top, w, crop_top + h))
            # Flou artistique élégant
            bg = bg.filter(ImageFilter.GaussianBlur(25))
        except Exception:
            bg = Image.new("RGBA", (w, h), (43, 45, 49))

    # Assombrir légèrement le fond pour que le texte blanc ressorte parfaitement
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 110))
    bg = Image.alpha_composite(bg, overlay)

    # 2. Avatar circulaire à gauche
    avatar_size = 150
    avatar_x = 55
    avatar_y = (h - avatar_size) // 2

    try:
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    except Exception:
        avatar = Image.new("RGBA", (avatar_size, avatar_size), (88, 101, 242))

    avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (avatar_size * 2, avatar_size * 2), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avatar_size * 2, avatar_size * 2), fill=255)
    mask = mask.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)

    circular_avatar = Image.new("RGBA", (avatar_size, avatar_size), (0, 0, 0, 0))
    circular_avatar.paste(avatar, (0, 0), mask=mask)
    bg.paste(circular_avatar, (avatar_x, avatar_y), mask=circular_avatar)

    # Cercle blanc subtil autour de l'avatar
    draw = ImageDraw.Draw(bg)
    draw.ellipse((avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size), outline=(255, 255, 255, 180), width=3)

    # 3. Textes à droite (avec polices TrueType garanties partout)
    try:
        font_title = ImageFont.truetype(FONT_BOLD_PATH, 50)
        font_sub = ImageFont.truetype(FONT_REGULAR_PATH, 22)
        font_guild = ImageFont.truetype(FONT_BOLD_PATH, 44)
    except Exception:
        # Fallback pour Pillow récent
        try:
            font_title = ImageFont.load_default(size=50)
            font_sub = ImageFont.load_default(size=22)
            font_guild = ImageFont.load_default(size=44)
        except Exception:
            font_title = font_sub = font_guild = ImageFont.load_default()

    text_x = 245
    # Bienvenue
    draw.text((text_x, 42), "Bienvenue", fill=(255, 255, 255), font=font_title)
    # sur le serveur Discord
    draw.text((text_x, 110), "sur le serveur Discord", fill=(225, 228, 232), font=font_sub)
    # Nom du serveur (ex: BVNekoo)
    display_guild = guild_name if guild_name and guild_name != "BV" else "BVNekoo"
    draw.text((text_x, 148), display_guild, fill=(255, 255, 255), font=font_guild)

    # 4. Découpe des coins arrondis
    card_mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, w, h), radius=22, fill=255)

    final_card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    final_card.paste(bg, (0, 0), mask=card_mask)

    output = io.BytesIO()
    final_card.save(output, format="PNG")
    output.seek(0)
    return output
