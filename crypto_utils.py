import hmac
import hashlib
import time
from config import SECRET_KEY

def create_verification_token(discord_id: int) -> str:
    """Crée un token signé contenant l'ID Discord et un timestamp (valide 1 heure)."""
    timestamp = int(time.time())
    message = f"{discord_id}:{timestamp}"
    signature = hmac.new(SECRET_KEY.encode(), message.encode(), hashlib.sha256).hexdigest()
    return f"{message}:{signature}"

def verify_token(token: str) -> int | None:
    """Vérifie le token. Retourne le discord_id si valide, None sinon."""
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        discord_id_str, timestamp_str, signature = parts
        discord_id = int(discord_id_str)
        timestamp = int(timestamp_str)
        
        # Expire après 1 heure (3600 secondes)
        if time.time() - timestamp > 3600:
            return None
            
        expected_sig = hmac.new(SECRET_KEY.encode(), f"{discord_id}:{timestamp}".encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(signature, expected_sig):
            return discord_id
    except Exception:
        return None
    return None
