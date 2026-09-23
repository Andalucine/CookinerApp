"""Change the plan of an account, for trying the app locally before payments exist.

Run from `backend/` (in Docker, with `docker compose exec api` in front):

    python -m scripts.set_plan beatriz@correo.es individual

PLAN is free, individual or family. The limits of the plan (recipes, people to share with)
are copied too. Development only: when payments arrive, the plan will change after paying.
"""

import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import User
from app.models.user import PLAN_LIMITS


class UnknownUser(Exception):
    pass


class UnknownPlan(Exception):
    pass


def set_plan(db: Session, email: str, plan: str) -> User:
    if plan not in PLAN_LIMITS:
        raise UnknownPlan
    user = db.scalar(select(User).where(User.email == email.strip().lower()))
    if user is None:
        raise UnknownUser
    user.plan = plan
    user.max_recipes = PLAN_LIMITS[plan]["max_recipes"]
    user.max_shared_with = PLAN_LIMITS[plan]["max_shared_with"]
    db.commit()
    return user


def main(args: list[str], db: Session | None = None) -> int:
    if len(args) != 2:
        print(__doc__)
        return 1
    email, plan = args
    session = db or SessionLocal()
    try:
        user = set_plan(session, email, plan)
    except UnknownPlan:
        print(f"✗ Plan desconocido: {plan}. Usa free, individual o family.")
        return 1
    except UnknownUser:
        print(f"✗ No hay ninguna cuenta con el correo {email}")
        return 1
    finally:
        if db is None:
            session.close()
    print(f"✓ {user.display_name} ({user.email}) tiene ahora el plan {user.plan}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
