from flask import Flask, request, jsonify, send_file, session
from g4f.client import Client
from fpdf import FPDF
from flask_cors import CORS
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure secret key for session management
CORS(app, origins=["https://jaideep-27.github.io"], supports_credentials=True)  # Updated CORS

client = Client()

@app.route('/generate-path', methods=['POST', 'OPTIONS'])
def generate_path():
    if request.method == 'OPTIONS':
        return jsonify({"message": "CORS preflight check successful"}), 200  # Handle OPTIONS requests

    data = request.get_json()
    
    # Extract and validate incoming data
    name = data.get('name')
    age = data.get('age')
    email = data.get('email')
    phone = data.get('phone')
    skills = data.get('skills')
    interests = data.get('interests')
    academic_background = data.get('academicBackground')
    additional_background = data.get('additionalBackground')
    goals = data.get('goals')

    # Required fields check
    if not all([name, age, email, phone, skills, interests, academic_background]):
        return jsonify({"error": "Please provide all required fields."}), 400

    prompt = (f"Suggest personalized learning paths for a user named {name}, aged {age}, "
              f"with skills in {skills}, interests in {interests}, and academic background in {academic_background}. "
              f"Additional details: {additional_background}. Goals: {goals}. "
              "Provide short and precise points only. Suggest necessary courses and colleges. "
              "Consider that the person is from India and use their information thoroughly."
              "Provide a detailed path in a simple, conversational tone with 15 to 20 points of 10 words each. "
              "Suggest suitable jobs and positions to pursue, and add emojis at random points.")

    try:
        # GPT-4 model for generating learning paths
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )

        if response.choices and response.choices[0].message.content:
            paths = response.choices[0].message.content.strip().split('\n')
            paths = [path.strip() for path in paths if path.strip()]
            formatted_paths = '\n'.join(paths)
        else:
            return jsonify({"error": "No paths generated."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    session['learning_paths'] = paths
    return jsonify({"paths": formatted_paths})

@app.route('/download-pdf', methods=['GET'])
def download_pdf():
    learning_paths = session.get('learning_paths', [])
    if not learning_paths:
        return jsonify({"error": "No learning paths available."}), 400

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Your Personalized Learning Paths", ln=True, align='C')
    pdf.ln(10)

    for i, path in enumerate(learning_paths, start=1):
        pdf.multi_cell(0, 10, txt=f"{i}. {path}")
        pdf.ln(2)

    pdf_file_path = "learning_path.pdf"
    pdf.output(pdf_file_path)

    try:
        response = send_file(pdf_file_path, as_attachment=True)
        os.remove(pdf_file_path)
        return response
    except Exception as e:
        return jsonify({"error": f"Error sending file: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use PORT from environment for Render.com
    app.run(debug=True, host="0.0.0.0", port=port)
