from flask import Flask, request, jsonify, send_from_directory
import os
import pandas as pd

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
DATA_STORAGE = "data.json"  # To store parsed data
IMAGES_FOLDER = "images"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER, exist_ok=True)


@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Validate file extension
        allowed_extensions = {'csv', 'xls', 'xlsx'}
        ext = file.filename.rsplit('.', 1)[-1].lower()

        if ext not in allowed_extensions:
            return jsonify({"error": "Invalid file format. Please upload a CSV or Excel file."}), 400

        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)

        # Parse the file and store data
        data = parse_file(file_path)
        return jsonify({"message": "File uploaded and processed", "data": data})

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


def parse_file(file_path):
    ext = file_path.split('.')[-1]
    if ext in ['csv', 'txt']:
        df = pd.read_csv(file_path)
    elif ext in ['xls', 'xlsx']:
        df = pd.read_excel(file_path)
    else:
        return {"error": "Unsupported file format"}

    # Check all columns for image extensions
    for column in df.columns:
        for idx, row in df.iterrows():
            cell_value = str(row[column])
            # Check if the cell contains a valid image extension
            if any(cell_value.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                # Update the cell with the Flask image URL
                df.at[idx, column] = f"/images/{cell_value}"

    # Convert the data to a dictionary and save as JSON
    data = df.to_dict(orient='records')
    with open(DATA_STORAGE, 'w') as f:
        f.write(pd.DataFrame(data).to_json(orient='records'))

    return data


@app.route('/data', methods=['GET'])
def get_data():
    if os.path.exists(DATA_STORAGE):
        with open(DATA_STORAGE, 'r') as f:
            return jsonify({"data": f.read()})
    return jsonify({"error": "No data available"}), 404


@app.route('/images/<filename>', methods=['GET'])
def get_image(filename):
    return send_from_directory(IMAGES_FOLDER, filename)


if __name__ == '__main__':
    app.run(debug=True)
