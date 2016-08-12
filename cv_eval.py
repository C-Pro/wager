import numpy as np
import tflearn
import json
import sys
import psycopg2
import requests
import logging
import time

j = None

#Send CV to parser and get parsed json back
try:
    headers = {"Accept": "application/json", "Origin": "https://emply.ru"}
    fname = sys.argv[1]
    files = [("files",("cv.doc",open(fname, 'rb'),'application/octet-stream'))]
    print("Uploading cv...")
    r = requests.post('https://api.emply.ru/v1/parser_demo/parse', headers=headers, files=files)
    file_id = r.json()[0]["id"]
    print("Waiting for cv to parse...")
    for i in range(0, 6):
        r = requests.get('https://api.emply.ru/v1/parser_demo/statuses?ids={}'.format(file_id), headers=headers)
        sj = r.json()
        print(sj)
        cv_id = sj[0]["cv"].get("id", 0) if sj[0]["cv"] else 0
        if cv_id > 0:
            r = requests.get('https://api.emply.ru/v1/parser_demo/cv_info?cv_id={}'.format(cv_id), headers=headers)
            j = r.json()
            break
        else:
            time.sleep(1+i)
    if not j:
        raise Exception("Tired to wait for CV to parse!")
except Exception:
    logging.exception('Failed to parse CV!')
    exit(1)


def print_prediction(p, wage):
    max_i = 0
    max_p = 0
    for i,x in enumerate(p):
        if x > 0:
            print("\t {}-{}: {}".format(i*10000,(i+1)*10000,x))
            if x > max_p:
                max_p = x
                max_i = i
    print('\tbest guess {}-{}: {}'.format(max_i*10000,(max_i+1)*10000, max_p))

# Build neural network
vector_len=1024 + 2
net = tflearn.input_data(shape=[None, vector_len])
net = tflearn.fully_connected(net, vector_len, activation='relu', regularizer='L2')
net = tflearn.fully_connected(net, (vector_len + 10) / 2, activation='relu', regularizer='L2')
net = tflearn.fully_connected(net, 10, activation='relu', regularizer='L2')
net = tflearn.regression(net)

# Define model
model = tflearn.DNN(net)
model.load('wager.model')

db = psycopg2.connect('host=localhost user=hr dbname=hr password=hr')
cur = db.cursor()

skill_ids = [x["skill_id"] for x in j["skill_ids"]]
cur.execute('select skills_to_bits(%s)', [skill_ids])
r = cur.fetchone()
bits = r[0]

try:
    area_name="Tatooine"
    for area_id in [x[-1]["id"] for x in j["favorite_areas_data"]]:
        if not area_id:
            continue
        cur.execute('select id,name from top_areas where area_id=%s',[area_id])
        r = cur.fetchone()
        if r:
            area_id = r[0]
            area_name = r[1]
            break
        if area_name == "Tatooine":
            raise Exception("No area found")
except:
    area_id=128
    area_name='Moscow'

try:
    rj = j["jobs"][:]
    rj.reverse()
    job_name = "Jabba Hutt's servant"
    for job_id in [x["job_id"] for x in j["favorite_jobs"]] + [x["job_id"] for x in rj]:
        if not job_id:
            continue
        cur.execute('select id,name from top_jobs where job_id=%s',[job_id])
        r = cur.fetchone()
        if r:
            job_id = r[0]
            job_name = r[1]
            break
    if job_name == "Jabba Hutt's servant":
        raise Exception("No jobs found")
except:
    job_id=128
    job_name='Sales manager'

X = [area_id, job_id] + [bits[i] for i in range(0,vector_len-2)]
p = model.predict([X])
print('{} in {}:'.format(job_name, area_name))
print_prediction(p[0], 0)


