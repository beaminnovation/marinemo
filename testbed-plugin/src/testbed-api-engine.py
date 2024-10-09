from flask import Flask, jsonify
from slices import slices_blueprint
from subscribers import subscribers_blueprint

app = Flask(__name__)

# Register blueprints
app.register_blueprint(slices_blueprint)
app.register_blueprint(subscribers_blueprint)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
