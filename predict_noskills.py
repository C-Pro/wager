import psycopg2
import numpy as np
import tflearn

def print_prediction(p, wage):
    max_i = 0
    max_p = 0
    for i,x in enumerate(p):
        if x > 0:
            #print("\t {}-{}: {}".format(i*10000,(i+1)*10000,x))
            if x > max_p:
                max_p = x
                max_i = i
    #print('\tbest guess {}-{}: {}'.format(max_i*10000,(max_i+1)*10000, max_p))
    #print('\treal wage {}'.format(wage))
    if (abs(wage-max_i*10000)<=5000) or (abs(wage-(max_i+1)*10000) <= 5000):
        return 1
    else:
        return 0


vector_len=2
net = tflearn.input_data(shape=[None, 2])
net = tflearn.fully_connected(net, 256, activation='relu', regularizer='L2')
net = tflearn.fully_connected(net, 133, activation='relu', regularizer='L2')
net = tflearn.fully_connected(net, 10, activation='relu', regularizer='L2')
net = tflearn.regression(net)

# Define model
model = tflearn.DNN(net)
model.load('wager_noskills.model')

db = psycopg2.connect('host=localhost user=hr dbname=hr password=hr')
cur = db.cursor()


sql = '''select top_area_id,
                top_job_id,
                wage,
                ta.name,
                tj.name
     from bitlearn b
          join top_areas ta on (ta.id = top_area_id)
          join top_jobs tj on (tj.id = top_job_id)
     where row_number > 1000000
     limit 100000'''
cur.execute(sql)
data = cur.fetchall()

sum_good = 0
for row in data:

    X = [row[0],row[1]]
    wage = row[2]
    area = row[3]
    job  = row[4]

    #print("{} в {}:".format(job,area))
    p = model.predict([X])
    sum_good += print_prediction(p[0], wage)

print(sum_good/len(data))

