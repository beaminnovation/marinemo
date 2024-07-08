# data_processing.py

from flask import Flask, jsonify, request
from kafka import KafkaConsumer
from kafka import KafkaProducer
import json
import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import pickle
import threading
import time

app = Flask(__name__)

# Configuration
KAFKA_TOPIC = 'your_kafka_topic'
KAFKA_BROKER = 'your_kafka_broker'
DATABASE_URI = 'your_database_uri'
MODEL_PATH = 'ml_model.pkl'
ALERTS_TABLE = 'alerts'

# Initialize Kafka consumer
consumer = KafkaConsumer(KAFKA_TOPIC, bootstrap_servers=KAFKA_BROKER)

# Initialize Kafka producer
producer = KafkaProducer(bootstrap_servers=KAFKA_BROKER)

# Initialize database connection
engine = create_engine(DATABASE_URI)

# Initialize Flask app
app = Flask(__name__)

def store_data_in_db(data):
    df = pd.DataFrame([data])
    df.to_sql('data', con=engine, if_exists='append', index=False)

def train_ml_model():
    while True:
        # Load historical data from the database
        df = pd.read_sql('data', con=engine)
        X = df.drop('target', axis=1)
        y = df['target']

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train model
        model = RandomForestClassifier()
        model.fit(X_train, y_train)

        # Evaluate model
        y_pred = model.predict(X_test)
        print(classification_report(y_test, y_pred))

        # Save the trained model
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(model, f)

        # Sleep for a period before retraining
        time.sleep(86400)  # Train model every 24 hours

def process_current_data():
    for message in consumer:
        data = json.loads(message.value.decode('utf-8'))
        store_data_in_db(data)

        # Load the trained model
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)

        # Prepare data for prediction
        df = pd.DataFrame([data])
        prediction = model.predict(df.drop('target', axis=1))

        # Store alert if needed
        if prediction == 1:  # Assuming 1 is the alert condition
            alert = {'alert': True, 'details': data}
            df_alert = pd.DataFrame([alert])
            df_alert.to_sql(ALERTS_TABLE, con=engine, if_exists='append', index=False)

@app.route('/alerts', methods=['GET'])
def get_alerts():
    # Fetch alerts from the database
    df_alerts = pd.read_sql(ALERTS_TABLE, con=engine)
    return jsonify(df_alerts.to_dict(orient='records'))

if __name__ == "__main__":
    # Start threads for data processing and model training
    threading.Thread(target=process_current_data).start()
    threading.Thread(target=train_ml_model).start()

    # Run Flask app
    app.run(host='0.0.0.0', port=5000)
