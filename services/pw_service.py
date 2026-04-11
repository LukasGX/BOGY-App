import sqlite3
import base64
import hashlib
from cryptography.fernet import Fernet
import os
from api.v1.deps import get_db
from fastapi import HTTPException

def get_cipher(unlock_key: str) -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(unlock_key.encode()).digest())
    return Fernet(key)

def verify_unlock_key(user_id: int, unlock_key: str) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT hashed_key FROM user_keys WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return bool(row and hashlib.sha256(unlock_key.encode()).hexdigest() == row["hashed_key"])

def has_user_key(user_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user_keys WHERE user_id = ?", (user_id,))
        return cursor.fetchone() is not None

def encrypt_secret_s(value: str, unlock_key: str) -> str:
    cipher = get_cipher(unlock_key)
    return cipher.encrypt(value.encode()).decode()

def decrypt_secret_s(encrypted_value: str, unlock_key: str) -> str:
    cipher = get_cipher(unlock_key)
    return cipher.decrypt(encrypted_value.encode()).decode()

def create_secret_s(user_id: int, name: str, value: str, unlock_key: str):
    with get_db() as conn:
        cursor = conn.cursor()
        # Check if user has a key set
        cursor.execute("SELECT hashed_key FROM user_keys WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        stored_hash = row["hashed_key"] if row else None
        
        if stored_hash:
            # Verify the key matches
            if hashlib.sha256(unlock_key.encode()).hexdigest() != stored_hash:
                raise HTTPException(status_code=400, detail="Invalid unlock key")
        else:
            # Set the key for the first time
            hashed_key = hashlib.sha256(unlock_key.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO user_keys (user_id, hashed_key) VALUES (?, ?)",
                (user_id, hashed_key)
            )
        
        encrypted_value = encrypt_secret_s(value, unlock_key)
        try:
            cursor.execute(
                "INSERT INTO secrets (user_id, name, encrypted_value) VALUES (?, ?, ?)",
                (user_id, name, encrypted_value)
            )
            return {"id": cursor.lastrowid, "name": name, "created": True}
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="Secret with this name already exists")

def get_secret_s(user_id: int, name: str, unlock_key: str):
    with get_db() as conn:
        cursor = conn.cursor()
        # Verify unlock key
        cursor.execute("SELECT hashed_key FROM user_keys WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row or hashlib.sha256(unlock_key.encode()).hexdigest() != row["hashed_key"]:
            raise HTTPException(status_code=400, detail="Invalid unlock key")
        
        cursor.execute(
            "SELECT id, name, encrypted_value, created_at, updated_at FROM secrets WHERE user_id = ? AND name = ?",
            (user_id, name)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Secret not found")
        try:
            decrypted_value = decrypt_secret_s(row["encrypted_value"], unlock_key)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid unlock key")
        return {
            "id": row["id"],
            "name": row["name"],
            "value": decrypted_value,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        }

def update_secret_s(user_id: int, name: str, value: str, unlock_key: str):
    with get_db() as conn:
        cursor = conn.cursor()
        # Verify unlock key
        cursor.execute("SELECT hashed_key FROM user_keys WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row or hashlib.sha256(unlock_key.encode()).hexdigest() != row["hashed_key"]:
            raise HTTPException(status_code=400, detail="Invalid unlock key")
        
        encrypted_value = encrypt_secret_s(value, unlock_key)
        cursor.execute(
            "UPDATE secrets SET encrypted_value = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND name = ?",
            (encrypted_value, user_id, name)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Secret not found")
        return {"name": name, "updated": True}

def delete_secret_s(user_id: int, name: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM secrets WHERE user_id = ? AND name = ?",
            (user_id, name)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Secret not found")
        return {"name": name, "deleted": True}

def list_secrets_s(user_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, created_at, updated_at FROM secrets WHERE user_id = ?",
            (user_id,)
        )
        rows = cursor.fetchall()
        return [{"id": row["id"], "name": row["name"], "created_at": row["created_at"], "updated_at": row["updated_at"]} for row in rows]

def change_unlock_key_s(user_id: int, old_unlock_key: str, new_unlock_key: str):
    if not verify_unlock_key(user_id, old_unlock_key):
        raise HTTPException(status_code=400, detail="Invalid old unlock key")
    
    with get_db() as conn:
        cursor = conn.cursor()
        # Get all secrets
        cursor.execute("SELECT id, name, encrypted_value FROM secrets WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        
        # Re-encrypt all with new key
        for row in rows:
            try:
                decrypted = decrypt_secret_s(row["encrypted_value"], old_unlock_key)
                new_encrypted = encrypt_secret_s(decrypted, new_unlock_key)
                cursor.execute(
                    "UPDATE secrets SET encrypted_value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_encrypted, row["id"])
                )
            except Exception:
                raise HTTPException(status_code=500, detail=f"Failed to re-encrypt secret {row['name']}")
        
        # Update the stored hash
        new_hashed_key = hashlib.sha256(new_unlock_key.encode()).hexdigest()
        cursor.execute(
            "INSERT OR REPLACE INTO user_keys (user_id, hashed_key) VALUES (?, ?)",
            (user_id, new_hashed_key)
        )
        
        return {"changed": True, "count": len(rows)}
    
def get_key_status_s(user_id):
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT hashed_key FROM user_keys WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return {"key_set": False}
        else:
            return {"key_set": True}