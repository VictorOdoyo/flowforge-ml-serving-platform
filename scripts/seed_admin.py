import asyncio
import os

from flowforge.core.security import hash_password
from flowforge.db.session import session_factory
from flowforge.models.enums import UserRole
from flowforge.models.user import User
from flowforge.repositories.user import UserRepository


async def seed_admin() -> None:
    email = os.getenv("FLOWFORGE_BOOTSTRAP_EMAIL", "admin@flowforge.local").lower()
    password = os.getenv("FLOWFORGE_BOOTSTRAP_PASSWORD")
    if password is None or len(password) < 12:
        raise RuntimeError("FLOWFORGE_BOOTSTRAP_PASSWORD must contain at least 12 characters")

    async with session_factory() as session:
        users = UserRepository(session)
        existing = await users.get_by_email(email)
        if existing is not None:
            print(f"Admin already exists: {email}")
            return
        await users.add(
            User(
                email=email,
                hashed_password=hash_password(password),
                full_name="FlowForge Administrator",
                role=UserRole.ADMIN,
                is_active=True,
            )
        )
        await session.commit()
        print(f"Created admin: {email}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
