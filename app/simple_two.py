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
    SELECT  PRODC.PRODC_NUMBR AS NO_OIPA,
            sum(vente.MNT_NOVL_ARGNT + vente.MNT_NOVL_RVD_EMIS) AS ENTREES
            
    FROM    VENTE

    JOIN PRODC ON VENTE.ID_CONS=PRODC.ID_PRODC

    WHERE   date(DATE_PROD) > %(debut)s AND
            date(DATE_PROD) < %(fin)s
            
    GROUP BY PRODC.PRODC_NUMBR;"""

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
    SELECT  PRODC.PRODC_NUMBR AS NO_OIPA,
            sum(vente.MNT_PRIM_EMIS + vente.MNT_INV_PRIM_EMIS) AS PRIME_EMIS
            
    FROM    VENTE

    JOIN PRODC ON VENTE.ID_CONS=PRODC.ID_PRODC

    WHERE   date(DATE_PROD) > %(debut)s AND
            date(DATE_PROD) < %(fin)s
            
    GROUP BY PRODC.PRODC_NUMBR;"""

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
    merged_table = pd.merge(df_epargne_LC, df_vie_LC, on="NO_OIPA", how="outer")
    return merged_table

merged_LC = merge_func()

all_columns = tuple(merged_LC.columns)
my_columns = [1, 2]
columns = [all_columns[i] for i in my_columns]


# STREAMLIT CODE

# SIDEBAR

side_bar = st.sidebar

side_bar.header("Choix de fitres")

ligne_affaires = side_bar.selectbox("Choisir la ligne d'affaires", columns)

df_select = pd.DataFrame(merged_LC[ligne_affaires], merged_LC["NO_OIPA"].astype(str))


# BODY

st.header("Ventes par coutier")
st.dataframe(merged_LC[["NO_OIPA", ligne_affaires]])

# alt_object_LC = alt.Chart(df_select.head(20)).mark_bar().encode(x=ligne_affaires, y=alt.Y("NO_OIPA", type="nominal", sort="-x"))

# alt_object_epargne_LC = alt.Chart(sorted_df_epargne_LC.head(20)).mark_bar().encode(x="ENTREES", y=alt.Y("NO_OIPA", sort="-x"))
# alt_object_vie_LC = alt.Chart(sorted_df_vie_LC.head(20)).mark_bar().encode(x="PRIME_EMIS", y=alt.Y("NO_OIPA", sort="-x"))

# st.altair_chart(alt_object_LC, use_container_width=True)


# if ligne_affaires == "Épargne":

#     st.header("Ventes par courtier - Épargne LC")

#     st.altair_chart(alt_object_epargne_LC, use_container_width=True)

# elif ligne_affaires == "Assurance":

#     st.header("Ventes par courtier - Assurance LC")

#     st.altair_chart(alt_object_vie_LC, use_container_width=True)


st.button('Re-run')


# progress_bar = st.sidebar.progress(0)
# status_text = st.sidebar.empty()

# last_rows = np.random.randn(1,1)
# chart = st.line_chart(last_rows)


# for i in range(1,101):
#     new_rows = last_rows[-1,:] + np.random.randn(5,1)
#     status_text.text("%i%% Complete"%i)
#     progress_bar.progress(i)
#     chart.add_rows(new_rows)

#     time.sleep(0.1)

# progress_bar.empty()

