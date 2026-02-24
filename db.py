import psycopg2
import pandas as pd
import streamlit as st

def get_conn():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=int(st.secrets.get("DB_PORT", 5432)),
        sslmode="require"
    )

def load_df(query, params=None):
    conn = get_conn()
    try:
        return pd.read_sql(query, conn, params=params)
    finally:
        conn.close()

def execute(query, params=None):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
        conn.commit()
    finally:
        conn.close()