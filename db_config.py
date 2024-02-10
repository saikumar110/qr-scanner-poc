from time import time, sleep

from fastapi.logger import logger
from sqlalchemy import (
    MetaData,
    create_engine, Table, Integer, VARCHAR, Column, TIMESTAMP, UniqueConstraint, func,
)

from sqlalchemy.orm import declarative_base, configure_mappers
import sqlalchemy as sql
import sqlalchemy.exc as sql_exec

use_sqlite = False  # Used in Table DDL as well
rdbms_type = "postgres"
execute_retry = True

db_name = 'postgres'
pg_user = 'postgres'
pg_pass = 'ramGLvp2k8q3FHx6qj3Y'
pg_host = 'qr-sc.c5q54jv9pfqi.ap-south-1.rds.amazonaws.com'
pg_port = 5432
engine_str = (
    f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{db_name}"
)
temp_engine_str = f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:{pg_port}"

if True:
    try:
        with create_engine(
                engine_str, isolation_level="AUTOCOMMIT"
        ).connect() as conn:
            res = conn.execute(
                f"select * from pg_database where datname='{db_name}';"
            )
            rows = res.rowcount > 0
            if not rows:
                # conn.execute('commit')
                res_db = conn.execute(f"CREATE DATABASE {db_name};")
                logger.info(f"DB created {db_name}. Response: {res_db.rowcount}")
    except Exception as exc:
        logger.error(exc)

metadata = MetaData()
Base = declarative_base(metadata=metadata)

n_table_mapping = "mappings"
s_table_mapping = Table(
    n_table_mapping,
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("q_id", VARCHAR(3000), nullable=False),
    Column("username", VARCHAR(500), nullable=True),
    Column("created_at", TIMESTAMP(timezone=True), server_default=func.current_timestamp()),
    Column("updated_at", TIMESTAMP(timezone=True), server_default=func.current_timestamp()),
    UniqueConstraint("q_id", "username", name=f"uq_{n_table_mapping}_xref"),
)

meta_engine = sql.create_engine(engine_str)
# Since only one table uses it so the call is only activated on DB initialization
configure_mappers()
metadata.create_all(meta_engine, checkfirst=True)

pool = sql.create_engine(
    engine_str,
    pool_size=50,
    max_overflow=20,
    pool_recycle=67,
    pool_timeout=30,
    echo=None,
)


def execute_query_v1(query, retry=2, wait_period=5, params=None, commit=False):
    if params is None:
        params = {}
    st = time()
    short_query = query[: int(len(query) * 0.25)]
    # logger.debug(f'Executing query...{short_query}...')
    # engine = sql.create_engine(engine_str)
    with pool.connect() as conn:
        try:

            result = conn.execute(query, params).mappings()
            # conn.execute(ins, dict_data, multi=multi)
            if commit:
                conn.execute("commit;")
        except sql_exec.OperationalError as e:
            if retry > 0:
                logger.info(f"Error for Query {short_query}: {e}")
                logger.info(
                    f"Retrying to execute query {short_query} after {wait_period} seconds"
                )
                sleep(wait_period)
                result = execute_query_v1(
                    query=query, retry=retry - 1, wait_period=wait_period
                )
            else:
                logger.error(f"Error for Query {short_query}: {e}", escalate=True)
        conn.close()

    # logger.debug(f"Time taken to execute query: {time() - st} secs")
    return result


def execute_query_old(query, params=None, commit=False):
    if params is None:
        params = {}
    st = time()
    # logger.debug(f'Executing query...{query[:int(len(query)*0.25)]}...')
    # engine = sql.create_engine(engine_str)
    with pool.connect() as conn:
        result = conn.execute(query, params=params)
        if commit:
            conn.execute("commit;")
        conn.close()

    # logger.debug(f"Time taken to execute query: {time() - st} secs")
    return result.mappings()


def execute_query(query, params=None, commit=False):
    if params is None:
        params = {}
    if execute_retry:
        return execute_query_v1(query, params=params, commit=commit)
    else:
        return execute_query_old(query, params=params, commit=commit)


class DbHandler:

    @classmethod
    def add_mapping(cls, qr_id):
        query = f"""INSERT INTO public.mappings (q_id, created_at, updated_at) 
        VALUES(%(qr_id)s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);"""
        return execute_query(query, params=dict(qr_id=qr_id))

    @classmethod
    def update_mapping(cls, qr_id, username):
        query = f"""UPDATE public.mappings  SET username = %(username)s WHERE q_id = %(qr_id)s RETURNING *;"""
        return execute_query(query, params=dict(qr_id=qr_id, username=username)).fetchone()

    @classmethod
    def get_qr_details(cls, qr_id):
        query = f"""SELECT * FROM public.mappings WHERE  q_id = %(qr_id)s ;"""
        return execute_query(query, params=dict(qr_id=qr_id)).fetchone()
