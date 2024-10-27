from flask import Flask, request, jsonify, send_file, session
from g4f.client import Client
from fpdf import FPDF
from flask_cors import CORS
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a random secret key for session management
CORS(app, origins=["https://YOUR_USERNAME.github.io"])

client = Client()

@app.route('/generate-path', methods=['POST'])
def generate_path():
    data = request.get_json()
    
    # Validate incoming data
    name = data.get('name')
    age = data.get('age')
    email = data.get('email')
    phone = data.get('phone')
    skills = data.get('skills')
    interests = data.get('interests')
    academic_background = data.get('academicBackground')
    additional_background = data.get('additionalBackground')
    goals = data.get('goals')

    # Check for required fields
    if not all([name, age, email, phone, skills, interests, academic_background]):
        return jsonify({"error": "Please provide all required fields."}), 400

    prompt = (f"Suggest personalized learning paths for a user named {name}, aged {age}, "
              f"with skills in {skills}, interests in {interests}, and academic background in {academic_background}. "
              f"Additional details: {additional_background}. Goals: {goals}. "
              "Provide short and precise points only. Suggest necessary courses and colleges. "
              "Keep in mind that the person asking this question is from India and use all his personal information thoroughly to provide solutions."
              "Detailed path in simple and creative words."
              "Use a conversational tone."
              "Atleast 15 to 20 points and each point should be 10 words."
              "Suggest suitable jobs and positions to pursue."
              "Use emojis in every line even in the points at random positions not just start or end.")
        
    try:
        # Using GPT-4 to generate the learning paths
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
        )
        
        # Check if response is valid
        if response.choices and response.choices[0].message.content:
            # Split the response into lines and join with new line characters
            paths = response.choices[0].message.content.strip().split('\n')
            paths = [path.strip() for path in paths if path.strip()]
            formatted_paths = '\n'.join(paths)  # Format as a single string
        else:
            return jsonify({"error": "No paths generated."}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Store the generated paths in the session
    session['learning_paths'] = paths
    return jsonify({"paths": formatted_paths})  # Return formatted string

@app.route('/download-pdf', methods=['GET'])
def download_pdf():
    # Retrieve the learning paths from the session
    learning_paths = session.get('learning_paths', [])
    if not learning_paths:
        return jsonify({"error": "No learning paths available."}), 400

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Your Personalized Learning Paths", ln=True, align='C')
    pdf.ln(10)  # Add a line break

    # Add each path to the PDF with better formatting and text wrapping
    for i, path in enumerate(learning_paths, start=1):
        pdf.multi_cell(0, 10, txt=f"{i}. {path}")  # Use multi_cell for text wrapping
        pdf.ln(2)  # Add a small space between paths

    pdf_file_path = "learning_path.pdf"
    pdf.output(pdf_file_path)

    # Ensure the file is closed before sending it
    response = send_file(pdf_file_path, as_attachment=True)
    
    # Optional: Remove the file after sending (if you want to manage space)
    os.remove(pdf_file_path)

    return response

if __name__ == '__main__':
    app.run(debug=True)
