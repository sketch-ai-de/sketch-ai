from sqlalchemy import create_engine


def create_sql_engine():
    engine = create_engine(
        "postgresql+psycopg2://postgres:P0$tgres@sketch-ai-postgres.postgres.database.azure.com:5432/postgres"
    )
    return engine
