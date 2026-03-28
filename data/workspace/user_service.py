"""User Service — handles user CRUD, authentication, and profile management."""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class User:
    user_id: str
    email: str
    name: str
    role: str = "user"
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


class UserNotFoundError(Exception):
    pass


class DuplicateEmailError(Exception):
    pass


class AuthenticationError(Exception):
    pass


class UserService:
    def __init__(self, db, cache=None, event_bus=None):
        self.db = db
        self.cache = cache or {}
        self.event_bus = event_bus
        self.logger = logging.getLogger("UserService")

    def create_user(
        self,
        email: str,
        name: str,
        password: str,
        role: str = "user",
        metadata: Dict = None,
    ) -> User:
        if self.db.find_by_email(email):
            raise DuplicateEmailError(f"Email {email} already registered")

        user_id = hashlib.sha256(f"{email}:{time.time()}".encode()).hexdigest()[:12]
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        user = User(
            user_id=user_id,
            email=email,
            name=name,
            role=role,
            metadata=metadata or {},
        )

        self.db.insert(
            "users",
            {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "password_hash": password_hash,
                "is_active": user.is_active,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
                "metadata": user.metadata,
            },
        )

        self._invalidate_cache(user_id)
        self._emit_event("user.created", {"user_id": user_id, "email": email})
        self.logger.info(f"Created user {user_id} ({email})")
        return user

    def get_user(self, user_id: str) -> User:
        cached = self._cache_get(f"user:{user_id}")
        if cached:
            return cached

        data = self.db.find("users", {"user_id": user_id})
        if not data:
            raise UserNotFoundError(f"User {user_id} not found")

        user = User(
            user_id=data["user_id"],
            email=data["email"],
            name=data["name"],
            role=data.get("role", "user"),
            is_active=data.get("is_active", True),
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0),
            metadata=data.get("metadata", {}),
        )

        self._cache_set(f"user:{user_id}", user)
        return user

    def get_user_by_email(self, email: str) -> User:
        cached = self._cache_get(f"email:{email}")
        if cached:
            return self.get_user(cached)

        data = self.db.find_by_email(email)
        if not data:
            raise UserNotFoundError(f"User with email {email} not found")

        self._cache_set(f"email:{email}", data["user_id"])
        return self.get_user(data["user_id"])

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> User:
        user = self.get_user(user_id)

        allowed_fields = {"name", "email", "role", "is_active", "metadata"}
        filtered = {k: v for k, v in updates.items() if k in allowed_fields}

        if "email" in filtered:
            existing = self.db.find_by_email(filtered["email"])
            if existing and existing["user_id"] != user_id:
                raise DuplicateEmailError(f"Email {filtered['email']} already in use")

        filtered["updated_at"] = time.time()
        self.db.update("users", {"user_id": user_id}, filtered)

        self._invalidate_cache(user_id)
        self._emit_event(
            "user.updated", {"user_id": user_id, "fields": list(filtered.keys())}
        )
        self.logger.info(f"Updated user {user_id}: {list(filtered.keys())}")
        return self.get_user(user_id)

    def delete_user(self, user_id: str) -> bool:
        user = self.get_user(user_id)
        self.db.delete("users", {"user_id": user_id})

        self._invalidate_cache(user_id)
        self._emit_event("user.deleted", {"user_id": user_id, "email": user.email})
        self.logger.info(f"Deleted user {user_id}")
        return True

    def list_users(
        self,
        page: int = 1,
        limit: int = 20,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        filters = {}
        if role is not None:
            filters["role"] = role
        if is_active is not None:
            filters["is_active"] = is_active

        total = self.db.count("users", filters)
        offset = (page - 1) * limit
        rows = self.db.find_many("users", filters, offset=offset, limit=limit)

        users = [
            User(
                user_id=r["user_id"],
                email=r["email"],
                name=r["name"],
                role=r.get("role", "user"),
                is_active=r.get("is_active", True),
                created_at=r.get("created_at", 0),
                updated_at=r.get("updated_at", 0),
                metadata=r.get("metadata", {}),
            )
            for r in rows
        ]

        return {
            "users": users,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }

    def search_users(self, query: str, limit: int = 10) -> List[User]:
        rows = self.db.search("users", query, limit=limit)
        return [
            User(
                user_id=r["user_id"],
                email=r["email"],
                name=r["name"],
                role=r.get("role", "user"),
                is_active=r.get("is_active", True),
            )
            for r in rows
        ]

    def authenticate(self, email: str, password: str) -> User:
        data = self.db.find_by_email(email)
        if not data:
            raise AuthenticationError("Invalid email or password")

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if data.get("password_hash") != password_hash:
            self._emit_event("auth.failed", {"email": email})
            raise AuthenticationError("Invalid email or password")

        if not data.get("is_active", True):
            raise AuthenticationError("Account is disabled")

        user = self.get_user(data["user_id"])
        self._emit_event("auth.success", {"user_id": user.user_id})
        return user

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> bool:
        data = self.db.find("users", {"user_id": user_id})
        if not data:
            raise UserNotFoundError(f"User {user_id} not found")

        old_hash = hashlib.sha256(old_password.encode()).hexdigest()
        if data.get("password_hash") != old_hash:
            raise AuthenticationError("Current password is incorrect")

        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        self.db.update(
            "users",
            {"user_id": user_id},
            {
                "password_hash": new_hash,
                "updated_at": time.time(),
            },
        )

        self._emit_event("user.password_changed", {"user_id": user_id})
        self.logger.info(f"Password changed for user {user_id}")
        return True

    def deactivate_user(self, user_id: str) -> User:
        return self.update_user(user_id, {"is_active": False})

    def activate_user(self, user_id: str) -> User:
        return self.update_user(user_id, {"is_active": True})

    def assign_role(self, user_id: str, role: str) -> User:
        valid_roles = {"user", "admin", "moderator", "viewer"}
        if role not in valid_roles:
            raise ValueError(f"Invalid role: {role}. Must be one of {valid_roles}")
        return self.update_user(user_id, {"role": role})

    def get_user_stats(self) -> Dict[str, Any]:
        total = self.db.count("users", {})
        active = self.db.count("users", {"is_active": True})
        by_role = {}
        for role in ["user", "admin", "moderator", "viewer"]:
            by_role[role] = self.db.count("users", {"role": role})

        return {
            "total": total,
            "active": active,
            "inactive": total - active,
            "by_role": by_role,
        }

    def _cache_get(self, key: str) -> Optional[Any]:
        if isinstance(self.cache, dict):
            entry = self.cache.get(key)
            if entry and entry.get("expires", 0) > time.time():
                return entry["value"]
        return None

    def _cache_set(self, key: str, value: Any, ttl: int = 300) -> None:
        if isinstance(self.cache, dict):
            self.cache[key] = {
                "value": value,
                "expires": time.time() + ttl,
            }

    def _invalidate_cache(self, user_id: str) -> None:
        if isinstance(self.cache, dict):
            self.cache.pop(f"user:{user_id}", None)

    def _emit_event(self, event_type: str, data: Dict) -> None:
        if self.event_bus:
            self.event_bus.emit(event_type, data)
