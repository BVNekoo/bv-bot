import io
from PIL import Image, ImageDraw, ImageFilter

def generate_welcome_card(avatar_bytes: bytes, banner_bytes: bytes | None = None, member_name: str = "", guild_name: str = "") -> io.BytesIO:
    """Génère la bannière personnalisée : bannière Discord du membre en fond + son avatar circulaire (sans aucun texte)."""
    w, h = 800, 270

    # 1. Fond : Bannière Discord du membre (ou avatar flouté si pas de bannière)
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
            # Flou d'arrière-plan élégant si l'utilisateur n'a pas de bannière
            bg = bg.filter(ImageFilter.GaussianBlur(25))
            # Léger assombrissement uniquement pour le flou de secours
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 70))
            bg = Image.alpha_composite(bg, overlay)
        except Exception:
            bg = Image.new("RGBA", (w, h), (43, 45, 49))

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

    # Contour blanc épuré autour de l'avatar
    draw = ImageDraw.Draw(bg)
    draw.ellipse((avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size), outline=(255, 255, 255, 230), width=3)

    # 3. Découpe avec coins arrondis
    card_mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(card_mask).rounded_rectangle((0, 0, w, h), radius=22, fill=255)

    final_card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    final_card.paste(bg, (0, 0), mask=card_mask)

    output = io.BytesIO()
    final_card.save(output, format="PNG")
    output.seek(0)
    return output
