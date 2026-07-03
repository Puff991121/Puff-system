from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.users import create_user, get_user_by_username


def main() -> None:
    with SessionLocal() as db:
        if get_user_by_username(db, settings.admin_username) is not None:
            print(f"管理员 {settings.admin_username!r} 已存在，无需重复创建。")
            return

        try:
            user = create_user(db, settings.admin_username, settings.admin_password)
        except SQLAlchemyError as exc:
            raise SystemExit(f"管理员写入失败：{exc}") from exc

        print(f"管理员 {user.username!r} 已写入 MySQL，用户 ID：{user.id}")


if __name__ == "__main__":
    main()
