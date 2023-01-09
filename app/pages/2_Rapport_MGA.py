import streamlit as st
import time
import numpy as np
import altair as alt

import snowflake.connector
import os
import pandas as pd
from pathlib import Path

import copy


# CONNECTION

R_SNOFLK_USER = os.getenv('R_SNOFLK_USER')

@st.experimental_singleton
def get_session():
    
    snowflake.connector.paramstyle = 'pyformat'

    conn = snowflake.connector.connect(
        user=R_SNOFLK_USER,
        password='N/A',
        account='ssq.canada-central.azure',
        authenticator='externalbrowser'
        )

    conn_cs = conn.cursor()
    return conn_cs

cs = get_session()


# VARIABLES

date_debut = '2021-12-31'
date_fin = '2022-11-27'
date_debut_vie_ssq = 20211231
date_fin_vie_ssq = 20221127


# QUERY LC ÉPARGNE

@st.experimental_singleton
def query_epargne():

    cs.execute('USE DATABASE M_ASSURANCE_INDIVIDUELLE')
    cs.execute('USE SCHEMA ACCES_BII_DATM')

    query_LC_epargne = """\
    SELECT  VENTE.DATE_PROD,
            PRODC.PRODC_NUMBR AS NO_OIPA,
            sum(vente.MNT_NOVL_ARGNT + vente.MNT_NOVL_RVD_EMIS) AS ENTREES
            
    FROM    VENTE

    JOIN PRODC ON VENTE.ID_CONS=PRODC.ID_PRODC

    WHERE   date(DATE_PROD) > %(debut)s AND
            date(DATE_PROD) < %(fin)s
            
    GROUP BY    VENTE.DATE_PROD,
                PRODC.PRODC_NUMBR;"""

    cs.execute(query_LC_epargne, {"debut": date_debut, "fin": date_fin})

    df_epargne = pd.DataFrame(cs.fetch_pandas_all())

    return df_epargne

df_epargne_LC = copy.deepcopy(query_epargne())

df_epargne_LC['NO_OIPA'] = df_epargne_LC['NO_OIPA'].str[4:10]

df_epargne_LC.dropna(axis=0, how='any', inplace=True)

df_epargne_LC['ENTREES'] = df_epargne_LC['ENTREES'].astype(float)

sorted_df_epargne_LC = df_epargne_LC.sort_values(by="ENTREES", ascending=False)


# QUERY ASSURANCE LC

@st.experimental_singleton
def query_vie():

    cs.execute('USE DATABASE M_ASSURANCE_INDIVIDUELLE')
    cs.execute('USE SCHEMA ACCES_BII_DATM')

    query_LC_vie = """\
    SELECT  VENTE.DATE_PROD,
            PRODC.PRODC_NUMBR AS NO_OIPA,
            sum(vente.MNT_PRIM_EMIS + vente.MNT_INV_PRIM_EMIS) AS PRIME_EMIS
            
    FROM    VENTE

    JOIN PRODC ON VENTE.ID_CONS=PRODC.ID_PRODC

    WHERE   date(DATE_PROD) > %(debut)s AND
            date(DATE_PROD) < %(fin)s
            
    GROUP BY    VENTE.DATE_PROD,
                PRODC.PRODC_NUMBR;"""

    cs.execute(query_LC_vie, {"debut": date_debut, "fin": date_fin})

    df_vie = pd.DataFrame(cs.fetch_pandas_all())

    return df_vie

df_vie_LC = copy.deepcopy(query_vie())

df_vie_LC['NO_OIPA'] = df_vie_LC['NO_OIPA'].str[4:10]

df_vie_LC.dropna(axis=0, how='any', inplace=True)

df_vie_LC['PRIME_EMIS'] = df_vie_LC['PRIME_EMIS'].astype(float)

sorted_df_vie_LC = df_vie_LC.sort_values(by="PRIME_EMIS", ascending=False)


# MERGE

@st.experimental_singleton
def merge_func():
    merged_table = pd.merge(df_epargne_LC, df_vie_LC, on=['DATE_PROD', 'NO_OIPA'], how="outer")
    return merged_table

merged_LC = merge_func()


# STREAMLIT CODE

# SIDEBAR

side_bar = st.sidebar

side_bar.header("Choix de fitres")

date_depuis = pd.to_datetime(side_bar.date_input("Choisir la date de début"))
date_jusqua = pd.to_datetime(side_bar.date_input("Choisir la date de fin"))

filtered_LC = merged_LC[(merged_LC['DATE_PROD'] > date_depuis) & (merged_LC['DATE_PROD'] < date_jusqua)]

# BODY

st.dataframe(filtered_LC)

st.button('Re-run')





