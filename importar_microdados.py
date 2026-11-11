
import sqlite3
import pandas as pd
from pathlib import Path









pasta = Path(__file__).resolve().parent

arquivo = pasta / "Tabela_Matricula_2025_V2.csv"
banco = pasta / "../censoescolarapi/censoescolar.db"

limite = 10000



estados = [
    "AL", "BA", "CE", "MA", "PB", "PE", "PI",
    "RN", "SE", "ES", "MG", "RJ", "SP"
]






colunas = {
    "NO_ENTIDADE": "no_entidade",
    "CO_ENTIDADE": "co_entidade",
    "NO_UF": "no_uf",
    "SG_UF": "sg_uf",
    "CO_UF": "co_uf",
    "NO_MUNICIPIO": "no_municipio",
    "CO_MUNICIPIO": "co_municipio",
    "NU_ANO_CENSO": "nu_ano_censo",
    "NO_REGIAO": "no_regiao",
    "CO_REGIAO": "co_regiao",
    "QT_MAT_BAS": "qt_mat_bas",
    "QT_MAT_INF": "qt_mat_inf",
    "QT_MAT_FUND": "qt_mat_fund",
    "QT_MAT_MED": "qt_mat_med",
    "QT_MAT_PROF": "qt_mat_prof",
    "QT_MAT_EJA": "qt_mat_eja",
    "QT_MAT_ESP": "qt_mat_esp"
}




colunas_csv = list(colunas.keys())
colunas_sql = list(colunas.values())






criar_tabela = """
CREATE TABLE IF NOT EXISTS tb_instituicao_ensino (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    no_entidade TEXT NOT NULL,
    co_entidade INTEGER NOT NULL UNIQUE,
    no_uf TEXT NOT NULL,
    sg_uf TEXT NOT NULL,
    co_uf INTEGER NOT NULL,
    no_municipio TEXT NOT NULL,
    co_municipio INTEGER NOT NULL,
    no_mesorregiao TEXT DEFAULT NULL,
    co_mesorregiao INTEGER DEFAULT NULL,
    no_microrregiao TEXT DEFAULT NULL,
    co_microrregiao INTEGER DEFAULT NULL,
    nu_ano_censo INTEGER NOT NULL,
    no_regiao TEXT,
    co_regiao INTEGER,
    qt_mat_bas INTEGER DEFAULT 0,
    qt_mat_inf INTEGER DEFAULT 0,
    qt_mat_fund INTEGER DEFAULT 0,
    qt_mat_med INTEGER DEFAULT 0,
    qt_mat_prof INTEGER DEFAULT 0,
    qt_mat_eja INTEGER DEFAULT 0,
    qt_mat_esp INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);
"""




sql = f"""
INSERT INTO tb_instituicao_ensino ({", ".join(colunas_sql)})
VALUES ({", ".join(["?"] * len(colunas_sql))})
ON CONFLICT(co_entidade) DO UPDATE SET
{", ".join(
    [f"{c} = excluded.{c}" for c in colunas_sql if c != "co_entidade"]
)};
"""











def importar():

    if not arquivo.exists():
        print("Arquivo CSV não encontrado!")
        raise FileNotFoundError(arquivo)

    lidos = 0
    processados = 0

    conexao = sqlite3.connect(banco)

    conexao.execute(criar_tabela)

    dados = pd.read_csv(
        arquivo,
        sep=";",
        usecols=colunas_csv,
        chunksize=limite,
        encoding="latin1",
        low_memory=False
    )

    numero = 0

    for df in dados:

        numero += 1
        lidos += len(df)

        df["SG_UF"] = df["SG_UF"].astype("string").str.strip().str.upper()

        df["NU_ANO_CENSO"] = pd.to_numeric(
            df["NU_ANO_CENSO"],
            errors="coerce"
        )

        df = df[
            (df["NU_ANO_CENSO"] == 2025) &
            (df["SG_UF"].isin(estados))
        ].copy()

        if len(df) == 0:
            print("Pagina", numero, "sem registros.")
            continue

        df = df.rename(columns=colunas)

        texto = [
            "no_entidade",
            "no_uf",
            "sg_uf",
            "no_municipio"
        ]

        for c in texto:
            df[c] = df[c].astype("string")

        numeros = [
            "co_entidade",
            "co_uf",
            "co_municipio",
            "nu_ano_censo",
            "co_regiao",
            "qt_mat_bas",
            "qt_mat_inf",
            "qt_mat_fund",
            "qt_mat_med",
            "qt_mat_prof",
            "qt_mat_eja",
            "qt_mat_esp"
        ]

        for c in numeros:
            df[c] = pd.to_numeric(
                df[c],
                errors="coerce"
            ).astype("Int64")

        df["no_mesorregiao"] = None
        df["co_mesorregiao"] = None
        df["no_microrregiao"] = None
        df["co_microrregiao"] = None

        df = df[colunas_sql]

        df = df.astype(object)
        df = df.where(pd.notna(df), None)

        lista_dados = []

        for linha in df.itertuples(index=False, name=None):
            lista_dados.append(linha)

        conexao.executemany(sql, lista_dados)
        conexao.commit()

        processados += len(lista_dados)

        print(
            "Pagina", numero,
            "-", len(lista_dados), "registros importados"
        )

    conexao.close()

    print("\nImportação finalizada!")
    print("Total de linhas lidas:", lidos)
    print("Total de registros processados:", processados)
    print("Banco utilizado:", banco)








if __name__ == "__main__":
    importar()
