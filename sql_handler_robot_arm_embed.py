from sqlalchemy import insert

from sql_handler_base import SQLHandlerBase


class SQLHandlerRobotArmEmbed(SQLHandlerBase):
    def insert_into_sql(self, embed_fields: list):
        print("embed_fields: ", embed_fields)
        with self._engine.connect() as connection:
            for field_dict in embed_fields:
                stmt = insert(self._sql_table).values(**field_dict)
                cursor = connection.execute(stmt)
                connection.commit()
