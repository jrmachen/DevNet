from flask import Flask, jsonify, request, Response
from functools import wraps
from classes.mycar import Car

app = Flask(__name__)


@app.route('/car', methods=['POST'])

def create_car():
    data = request.json
    try:
        make = data.get('make')
        model = data.get('model')
        year = data.get('year')
        car = Car(make, model, year)

        if not make or not model or not year:
            return jsonify({'error': 'Make, model, and year are required'}), 400

        car = Car(make, model, year)
        return jsonify({'message': 'Car created successfully', 'car': car.get_info()})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


def protected():
    return jsonify({'message': 'This is a protected route'})

###
# Authentication logic
###

VALID_USERNAME = 'admin'
VALID_PASSWORD = 'secret'

def check_authentication(username, password):
    return username == VALID_USERNAME and password == VALID_PASSWORD

def authenitcate():
    auth = request.authorization
    if not auth or not check_authentication(auth.username, auth.password):
        return jsonify({'error': 'Invalid credentials'}), 401

def require_authentication(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_authentication(auth.username, auth.password):
            return jsonify({'error': 'Invalid credentials'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/protected')
@require_authentication
def protected():
    return jsonify({'message': 'This is a protected route'})

if __name__ == '__main__':
    app.run(debug=True)


