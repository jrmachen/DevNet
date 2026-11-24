from flask import Flask, jsonify, request
from classes.carclass import Car

app = Flask(__name__)

@app.route('/api/car', methods=['POST'])
def createcar():
    data = request.json
    try:
        make = data.get('make')
        model = data.get('model')
        year = data.get('year')

        if not all([make, model, year]):
            return jsonify({'error': 'Missing required fields'}), 400

        car = Car(make, model, year)
        return jsonify({'car': car.__dict__}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()
