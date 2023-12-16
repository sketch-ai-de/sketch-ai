from sqlalchemy import insert

from sql_handler_base import SQLHandlerBase


class SQLHandlerSoftwareEmbed(SQLHandlerBase):
    def insert_into_sql(self, embed_fields: list):
        with self._engine.connect() as connection:
            for field_dict in embed_fields:
                stmt = insert(self._sql_table).values(**field_dict)
                cursor = connection.execute(stmt)
                connection.commit()
