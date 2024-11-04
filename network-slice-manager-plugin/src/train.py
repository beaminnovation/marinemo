import pandas as pd
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from joblib import dump

# load the datasets
cpe_high = pd.read_csv('CPE_high.csv')
cpe_medium = pd.read_csv('CPE_medium.csv')
cpe_normal = pd.read_csv('CPE_normal.csv')

# label the datasets
cpe_high['traffic_type'] = 'high'
cpe_medium['traffic_type'] = 'medium'
cpe_normal['traffic_type'] = 'normal'

# balance the training data (downsample to the minimum class count)
min_class_count = min(cpe_high.shape[0], cpe_medium.shape[0], cpe_normal.shape[0])
cpe_high_balanced = cpe_high.sample(min_class_count, random_state=42)
cpe_medium_balanced = cpe_medium.sample(min_class_count, random_state=42)
cpe_normal_balanced = cpe_normal.sample(min_class_count, random_state=42)

# combine the balanced training datasets
train_data = pd.concat([cpe_high_balanced, cpe_medium_balanced, cpe_normal_balanced])

# define the ML model features and the target
features = ['URLLC_Sent_thrp_Mbps', 'URLLC_BytesSent', 'URLLC_BytesReceived', 'URLLC_Received_thrp_Mbps']
X = train_data[features]
y = train_data['traffic_type']

# separate each class
X_high = X[y == 'high']
X_medium = X[y == 'medium']
X_normal = X[y == 'normal']

y_high = y[y == 'high']
y_medium = y[y == 'medium']
y_normal = y[y == 'normal']

# split each class separately
X_train_high, X_test_high, y_train_high, y_test_high = train_test_split(X_high, y_high, test_size=0.2, random_state=42)
X_train_medium, X_test_medium, y_train_medium, y_test_medium = train_test_split(X_medium, y_medium, test_size=0.2, random_state=42)
X_train_normal, X_test_normal, y_train_normal, y_test_normal = train_test_split(X_normal, y_normal, test_size=0.2, random_state=42)

# combine the splits to form the final train and test sets
X_train = pd.concat([X_train_high, X_train_medium, X_train_normal])
X_test = pd.concat([X_test_high, X_test_medium, X_test_normal])
y_train = pd.concat([y_train_high, y_train_medium, y_train_normal])
y_test = pd.concat([y_test_high, y_test_medium, y_test_normal])

# normalize the training and testing data
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# train multiple classifiers
clf_rf = RandomForestClassifier(n_estimators=1000, random_state=42)
clf_lr = LogisticRegression(max_iter=1000, random_state=42)
clf_svc = SVC(kernel='linear', probability=True, random_state=42)

# create an ensemble of the classifiers
clf_ensemble = VotingClassifier(estimators=[
    ('rf', clf_rf),
    ('lr', clf_lr),
    ('svc', clf_svc)
], voting='soft')

# train the ensemble classifier
clf_ensemble.fit(X_train_scaled, y_train)

# evaluate the ensemble classifier
y_test_pred = clf_ensemble.predict(X_test_scaled)

# generate the classification report as a dictionary
report = classification_report(y_test, y_test_pred, output_dict=True)

# format the classification report to show 5 decimal places
formatted_report = {}
for label, scores in report.items():
    if isinstance(scores, dict):
        formatted_report[label] = {metric: f"{score:.5f}" if isinstance(score, float) else score
                                   for metric, score in scores.items()}
    else:
        formatted_report[label] = f"{scores:.5f}" if isinstance(scores, float) else scores

# print the formatted classification report
print("Ensemble Classifier Performance:")
for label, scores in formatted_report.items():
    if isinstance(scores, dict):
        print(f"{label}:")
        for metric, score in scores.items():
            print(f"  {metric}: {score}")
    else:
        print(f"{label}: {scores}")

# save the trained model and scaler
dump(clf_ensemble, 'traffic_model.joblib')
dump(scaler, 'scaler.joblib')

print("Model training complete and saved to 'traffic_model.joblib' and 'scaler.joblib'")
