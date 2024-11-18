import requests
import sqlalchemy
import sqlite3
from flask import Flask, session, url_for, request, redirect, jsonify
import pandas as pd

app = Flask(__name__)
dictCoordenadas= {}

DATABASE_LOCATION = "sqlite:///dna_results.sqlite"
@app.route('/', methods=["GET"])
def home():
    stats = stats()
    return "Prueba de MELI"+ stats
    
@app.route('/mutant', methods=['POST'])
def mutant():
    res = request.get_json()
    dna = res["dna"]
    dna_result = is_mutant(dna)
    
    if dna_result == "Mutant":
        saveInDB(dna, "Mutant")
        dictCoordenadas.clear()
        return jsonify({"message": "Mutant"}), 200 
    elif dna_result == "Human":
        saveInDB(dna, "Human")
        dictCoordenadas.clear()
        return jsonify({"message": "Human"}), 403 
    else: 
        dictCoordenadas.clear()
        return jsonify({"message": "Invalid Sequence"}), 403
    
@app.route('/stats', methods=['GET'])
def stats():
     engine = sqlalchemy.create_engine(DATABASE_LOCATION)
     conn = sqlite3.connect("dna_results.sqlite")
     cursor = conn.cursor()
     
     query = """
            SELECT
                SUM(CASE WHEN result = 'Mutant' THEN 1 ELSE 0 END) AS count_mutant_dna,
                SUM(CASE WHEN result = 'Human' THEN 1 ELSE 0 END) AS count_human_dna,
                CAST(SUM(CASE WHEN result = 'Mutant' THEN 1 ELSE 0 END) AS FLOAT) / 
                NULLIF(SUM(CASE WHEN result = 'Human' THEN 1 ELSE 0 END), 0) AS ratio
            FROM dna_results;
            """
            
    
     cursor.execute(query)
     resultado = cursor.fetchone()
     data = {
    "count_mutant_dna": resultado[0],
    "count_human_dna": resultado[1],
    "ratio": round(resultado[2], 2) if resultado[2] is not None else None
    }
     return data

def saveInDB(dna, result):
     engine = sqlalchemy.create_engine(DATABASE_LOCATION)
     conn = sqlite3.connect("dna_results.sqlite")
     cursor = conn.cursor()
     
     dna_info = ["".join(dna), result]
  
     dna_database = pd.DataFrame(columns= ["dna", "result"])
     
     newRow= pd.DataFrame({"dna": [dna_info[0]], "result": [dna_info[1]]})
     dna_database = pd.concat([dna_database, newRow], ignore_index=True)

          
     print(dna_database)
     sql_query = """
     CREATE TABLE IF NOT EXISTS dna_results(
         result VARCHAR(200),
         dna VARCHAR(200),
         CONSTRAINT primary_key_constraint PRIMARY KEY (dna)
         ) """
     cursor.execute(sql_query)
     print("Opened database successfully")
     
     try:
         dna_database.to_sql("dna_results", engine, index = False, if_exists = 'append')
     except:
         print("DNA sequence already exists")


def checkMatrix(dna):
  for i,fila in  enumerate(dna):
    for j,elemento in  enumerate(fila):
      dictCoordenadas.setdefault(elemento, []).append((i, j))

    
def verificar_consecutivas(coordenadas):
  # Comprobar si las coordenadas son consecutivas en fila
  coordenadas.sort()  # Ordenar por columna (para que las filas queden en orden)
  for i in range(len(coordenadas) - 3):
      if (coordenadas[i+1][0] == coordenadas[i][0] and 
          coordenadas[i+2][0] == coordenadas[i][0] and
          coordenadas[i+3][0] == coordenadas[i][0] and
          coordenadas[i+1][1] == coordenadas[i][1] + 1 and
          coordenadas[i+2][1] == coordenadas[i][1] + 2 and
          coordenadas[i+3][1] == coordenadas[i][1] + 3):
          return True  # Hay 4 consecutivos en una fila
  # Comprobar si las coordenadas son consecutivas en columna
  for i in range(len(coordenadas) - 3):
      if (coordenadas[i+1][1] == coordenadas[i][1] and 
          coordenadas[i+2][1] == coordenadas[i][1] and
          coordenadas[i+3][1] == coordenadas[i][1] and
          coordenadas[i+1][0] == coordenadas[i][0] + 1 and
          coordenadas[i+2][0] == coordenadas[i][0] + 2 and
          coordenadas[i+3][0] == coordenadas[i][0] + 3):
          return True  # Hay 4 consecutivos en una columna
  # Comprobar si las coordenadas son consecutivas en diagonal
  for i in range(len(coordenadas) - 3):
      if (coordenadas[i+1][0] == coordenadas[i][0] + 1 and 
          coordenadas[i+1][1] == coordenadas[i][1] + 1 and
          coordenadas[i+2][0] == coordenadas[i][0] + 2 and 
          coordenadas[i+2][1] == coordenadas[i][1] + 2 and
          coordenadas[i+3][0] == coordenadas[i][0] + 3 and 
          coordenadas[i+3][1] == coordenadas[i][1] + 3):
          return True  # Hay 4 consecutivos en una diagonal
  return False  # No hay consecutivos
  

def is_mutant(dna):

    checkMatrix(dna)

    mutantCounter = 0
    
    for letra, coordenadas in dictCoordenadas.items():
        if letra in ["A","T","C","G"]:
          if verificar_consecutivas(coordenadas):
              mutantCounter = mutantCounter+1
        else:
            return "Invalid"

    if mutantCounter >= 2:
        return "Mutant"
    return "Human"



    
if __name__ == "__main__":
    app.run(debug=True)