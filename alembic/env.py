import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.base import Base
from app.db.models import *  # 모든 모델 임포트

target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """환경 변수에서 데이터베이스 URL 가져오기 (.env 파일 우회)"""

    # .env 파일 대신 직접 환경변수 설정 (인코딩 문제 우회)
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = (
            "postgresql+psycopg2://postgres:Lqp1o2k3!!!@db.mevuhulrdzeqwojrjatl.supabase.co:5432/postgres"
        )

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        # Supabase 연결 정보로 URL 구성
        host = "db.mevuhulrdzeqwojrjatl.supabase.co"
        port = "5432"
        name = "postgres"
        user = "postgres"
        password = "Lqp1o2k3!!!"
        database_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"

    return database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # 환경변수에서 DATABASE_URL 직접 사용 (configparser 우회)
    database_url = get_database_url()

    # configparser interpolation 문제 해결을 위해 직접 engine 생성
    connectable = engine_from_config(
        {"sqlalchemy.url": database_url},  # 직접 딕셔너리로 전달
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
