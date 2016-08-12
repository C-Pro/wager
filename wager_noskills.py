import psycopg2
import numpy as np
import tflearn

# Build neural network
vector_len=2
net = tflearn.input_data(shape=[None, 2])
net = tflearn.fully_connected(net, 256, activation='relu', regularizer='L2')
net = tflearn.fully_connected(net, 133, activation='relu', regularizer='L2')
net = tflearn.fully_connected(net, 10, activation='relu', regularizer='L2')
net = tflearn.regression(net)

# Define model
model = tflearn.DNN(net)

db = psycopg2.connect('host=localhost user=hr dbname=hr password=hr')
cur = db.cursor()

for page in range(0,1000):
    print('Iteration {}'.format(page))
    sql = '''select top_area_id,
                    top_job_id,
                    wage
        from bitlearn
        where row_number < 1000000
        limit 10000
        offset %s'''
    cur.execute(sql, [page*10000])
    data = cur.fetchall()

    if len(data) < 10000:
        print("Done learning! PROM!")
        break

    X = np.array([[x[0],x[1],]  for x in data], dtype=np.float32)
    Y = np.array([[1.0 if (abs((i*10000+5000) - x[2])<10000) or (i==9 and x[2]>95000) else 0.0 for i in range(0,10)] for x in data], dtype=np.float32)


    # Start training (apply gradient descent algorithm)
    model.fit(X, Y, n_epoch=3, batch_size=64, validation_set=0.1, show_metric=True)
    model.save('wager_noskills.model')
