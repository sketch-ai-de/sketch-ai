from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    create_engine,
    select,
    text,
)
from sqlalchemy.orm import declarative_base, mapped_column


class SQLHandlerBase:
    def __init__(
        self,
        engine_config="postgresql+psycopg2://postgres:P0$tgres@sketch-ai-postgres.postgres.database.azure.com:5432/postgres",
        engine=None,
        table_name=None,
        sql_fields=None,
        logger=None,
    ):
        self._engine = engine or create_engine(engine_config)
        self._sql_fields = self.get_sql_fields(sql_fields)
        self._base = None
        self._table_name = table_name
        self._sql_table = None
        self._logger = logger

    def get_sql_fields(self, sql_fields):
        for field in sql_fields:
            datatype = sql_fields[field]["datatype"]
            if datatype == "str":
                sql_fields[field]["sql_datatype"] = String
            elif datatype == "float":
                sql_fields[field]["sql_datatype"] = Float
            elif datatype == "int":
                sql_fields[field]["sql_datatype"] = Integer
            elif datatype == "bool":
                sql_fields[field]["sql_datatype"] = Boolean
            elif datatype == "vector":
                sql_fields[field]["sql_datatype"] = Vector(
                    int(sql_fields[field]["datatype_extra"]["dim"])
                )

        return sql_fields

    def create_base(self):
        self._base = declarative_base()
        self._base.metadata.bind = self._engine
        self._base.metadata.reflect(self._base.metadata.bind)

        class SQLTable(self._base):
            sql_fields = self._sql_fields
            __tablename__ = self._table_name
            __table_args__ = (PrimaryKeyConstraint("id"),)
            __table_args__ = {"extend_existing": True}
            id = mapped_column(
                Integer,
                primary_key=True,
                autoincrement=True,
                comment=f"Unique identifier for the {self._table_name}",
            )
            # print("sql_fields: ", sql_fields)
            for field in sql_fields.keys():
                if field != "id":
                    if "ForeignKey" in sql_fields[field]["sql_extra"].keys():
                        locals()[field] = mapped_column(
                            Integer,
                            ForeignKey(
                                str(sql_fields[field]["sql_extra"]["ForeignKey"])
                            ),
                            nullable=False,
                            comment=sql_fields[field]["description"],
                        )

                    else:
                        locals()[field] = mapped_column(
                            sql_fields[field]["sql_datatype"],
                            comment=sql_fields[field]["description"],
                        )

        self._sql_table = SQLTable

    def create_table(self):
        with self._engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

        self.create_base()
        self._logger.info(f"Create table: {self._table_name}")
        self._base.metadata.create_all(self._engine)

    def get_id(self, name):
        name_id = None
        with self._engine.connect() as connection:
            connection.commit()
            metadata = MetaData()
            table = Table(self._table_name, metadata, autoload_with=self._engine)
            stmt = select(table.c.id).where(table.c.product_name == name)
            with self._engine.connect() as conn:
                name_id = conn.execute(stmt).fetchall()

        return name_id[0][0] if name_id else None
