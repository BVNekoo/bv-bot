import io
from PIL import Image, ImageDraw

def generate_welcome_card(avatar_bytes: bytes, member_name: str = "", guild_name: str = "") -> io.BytesIO:
    """Génère uniquement la photo de profil circulaire avec le contour couleur Discord #5865F2, sans aucun texte."""
    # Rendu haute définition (800x800) avec fond transparent
    w2, h2 = 800, 800
    img = Image.new("RGBA", (w2, h2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    avatar_size2 = 720
    avatar_x2 = (w2 - avatar_size2) // 2
    avatar_y2 = (h2 - avatar_size2) // 2

    # Cercle #5865f2 (RGB: 88, 101, 242)
    ring_pad = 14
    ring_bbox = (
        avatar_x2 - ring_pad,
        avatar_y2 - ring_pad,
        avatar_x2 + avatar_size2 + ring_pad,
        avatar_y2 + avatar_size2 + ring_pad
    )
    draw.ellipse(ring_bbox, outline=(88, 101, 242), width=18)

    # Découpe circulaire de l'avatar
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

    # Réduction à 400x400 avec anti-aliasing Lanczos
    final_img = img.resize((400, 400), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    final_img.save(output, format="PNG")
    output.seek(0)
    return output
