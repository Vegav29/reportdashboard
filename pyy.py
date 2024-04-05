from flask import Flask, render_template, request, jsonify
import logging
from datetime import datetime
from pymongo import MongoClient

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.ERROR)

# MongoDB Configuration
mongo_config = {
    'connection_string': 'mongodb+srv://vega:vega2003@app.ecjlw4l.mongodb.net/',  # MongoDB Atlas connection string
    'database': 'cluster0',
    'collection': 'user'
}

def connect_to_database():
    try:
        client = MongoClient(mongo_config['connection_string'])
        db = client[mongo_config['database']]
        app.logger.info('Successfully connected to the database.')
        return db[mongo_config['collection']]
    except Exception as e:
        app.logger.error('Failed to connect to the database: %s', e)
        return None

# Function to parse and format date strings
def format_date(date_string):
    try:
        # Parse the input date string
        date_obj = datetime.strptime(date_string, '%Y-%m-%d')
        # Format the date in 'YYYY/MM/DD' format
        formatted_date = date_obj.strftime('%Y/%m/%d')
        return formatted_date
    except ValueError:
        return None  # Handle invalid date format gracefully

# Route to render the HTML template
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle data retrieval
@app.route('/data', methods=['GET'])
def get_data():
    try:
        collection = connect_to_database()
        if collection is None:
            return jsonify({'error': 'Failed to connect to the database'}), 500

        from_date = request.args.get('from')
        to_date = request.args.get('to')
        frequency = request.args.get('frequency')

        app.logger.info('From Date: %s, To Date: %s, Frequency: %s', from_date, to_date, frequency)

        # Format dates according to server-side requirements
        formatted_from_date = format_date(from_date)
        formatted_to_date = format_date(to_date)

        app.logger.info('Formatted From Date: %s, Formatted To Date: %s', formatted_from_date, formatted_to_date)

        query = [
            {
                '$match': {
                    'Date': {
                        '$gte': formatted_from_date,
                        '$lte': formatted_to_date
                    }
                }
            },
            {
                '$addFields': {
                    'parsedDate': {'$toDate': '$Date'}  # Convert Date field to Date type
                }
            },
            {
                '$group': {
                    '_id': {
                        'license_plate': '$LicensePlate',
                        'make': '$Make',
                        'vin': '$VIN',
                        'model': '$Model',
                        'type': '$Type',
                        'Year': {'$year': '$parsedDate'},  # Extract year from parsedDate
                        'Month': {'$month': '$parsedDate'}  # Extract month from parsedDate
                    },
                    'Totalmiles': {'$sum': '$MilesDriven'}
                }
            }
        ]

        # Log the constructed MongoDB query
        app.logger.info('MongoDB Query: %s', query)

        data = list(collection.aggregate(query))
        app.logger.info('Data fetched successfully: %s', data)  # Add this line to log the fetched data

        return jsonify(data)

    except Exception as e:
        # Log the error
        app.logger.error('An error occurred: %s', e)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
