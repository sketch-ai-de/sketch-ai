from sqlalchemy import MetaData, Table, insert, select

from sql_handler_base import SQLHandlerBase


class SQLHandlerPLC(SQLHandlerBase):
    def get_id(self, name):
        id = None
        with self._engine.connect() as connection:
            connection.commit()
            metadata = MetaData()
            table = Table(self._table_name, metadata, autoload_with=self._engine)
            stmt = select(table.c.id).where(table.c.product_name == name)
            with self._engine.connect() as conn:
                id = conn.execute(stmt).fetchall()

        return id[0][0] if id else None

    def insert_into_sql(self, insert_dict):
        _tmp_description_long = ""
        for dev_key in insert_dict.keys():
            _tm_tmp_description_longp = (
                _tmp_description_long
                + "\n"
                + str(dev_key)
                + ": "
                + str(insert_dict[dev_key])
            )
        insert_dict["product_description_long"] = _tmp_description_long
        insert_dict["product_description"] = (
            "Company name: "
            + insert_dict["company_name"]
            + "\n"
            + "Product name: "
            + insert_dict["product_name"]
            + "\n"
            + "Article number: "
            + insert_dict["article_number"]
            + "\n"
            + "Product description: "
            + insert_dict["product_description"]
            + "\n"
            + "Mandatory additional components: "
            + insert_dict["must_have_components"]
        )
        stmt = insert(self._sql_table).values(**insert_dict)
        with self._engine.connect() as connection:
            cursor = connection.execute(stmt)
            connection.commit()
