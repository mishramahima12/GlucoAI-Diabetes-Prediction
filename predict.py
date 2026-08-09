from flask import Flask, render_template, request, send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from flask import redirect
import joblib
import pandas as pd
import mysql.connector

app = Flask(__name__)

# Load ML Model
model = joblib.load("diabetes_model.pkl")

# Database Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="ashu",
    database="diabetes_db"
)

cursor = conn.cursor()
# ===========================
# Home Page
# ===========================
@app.route("/")
def home():
    return render_template("index.html")


# ===========================
# Prediction Page
# ===========================
@app.route("/predict", methods=["GET", "POST"])
def predict():

    # Open Prediction Page
    if request.method == "GET":
        return render_template("predict.html")

    # Get Form Data
    name = request.form["name"]
    gender = request.form["gender"]
    age = int(request.form["age"])
    hypertension = int(request.form["hypertension"])
    heart_disease = int(request.form["heart_disease"])
    smoking_history = request.form["smoking_history"]
    bmi = float(request.form["bmi"])
    hba1c = float(request.form["hba1c"])
    glucose = int(request.form["glucose"])

    # Prepare data for ML model
    sample = pd.DataFrame({
        "gender": [gender],
        "age": [age],
        "hypertension": [hypertension],
        "heart_disease": [heart_disease],
        "smoking_history": [smoking_history],
        "bmi": [bmi],
        "HbA1c_level": [hba1c],
        "blood_glucose_level": [glucose]
    })

    # Prediction
    prediction = model.predict(sample)[0]
    probability = model.predict_proba(sample)[0]

    result = "Diabetic" if prediction == 1 else "Not Diabetic"
    confidence = round(max(probability) * 100, 2)

    # SQL Query
    query = """
    INSERT INTO patient_predictions
    (
        patient_name,
        gender,
        age,
        hypertension,
        heart_disease,
        smoking_history,
        bmi,
        hba1c,
        blood_glucose,
        prediction,
        confidence
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        name,
        gender,
        age,
        hypertension,
        heart_disease,
        smoking_history,
        bmi,
        hba1c,
        glucose,
        result,
        confidence
    )

    # Save to MySQL
    try:
        cursor.execute(query, values)
        conn.commit()
        print("✅ Data inserted successfully!")

    except mysql.connector.Error as err:
        print("❌ MySQL Error:", err)

    return render_template(
        "result.html",
        prediction=result,
        confidence=confidence
    )
    # Get form data
    name = request.form["name"]
    gender = request.form["gender"]
    age = int(request.form["age"])
    hypertension = int(request.form["hypertension"])
    heart_disease = int(request.form["heart_disease"])
    smoking_history = request.form["smoking_history"]
    bmi = float(request.form["bmi"])
    hba1c = float(request.form["hba1c"])
    glucose = int(request.form["glucose"])

    # Prepare data for model
    sample = pd.DataFrame({
        "gender": [gender],
        "age": [age],
        "hypertension": [hypertension],
        "heart_disease": [heart_disease],
        "smoking_history": [smoking_history],
        "bmi": [bmi],
        "HbA1c_level": [hba1c],
        "blood_glucose_level": [glucose]
    })

    # Prediction
    prediction = model.predict(sample)[0]
    probability = model.predict_proba(sample)[0]

    result = "Diabetic" if prediction == 1 else "Not Diabetic"
    confidence = round(max(probability) * 100, 2)

    # Save to database
    query = """
    INSERT INTO patient_predictions
    (
        patient_name,
        gender,
        age,
        hypertension,
        heart_disease,
        smoking_history,
        bmi,
        hba1c,
        blood_glucose,
        prediction,
        confidence
    )
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        name,
        gender,
        age,
        hypertension,
        heart_disease,
        smoking_history,
        bmi,
        hba1c,
        glucose,
        result,
        confidence
    )

    cursor.execute(query, values)
    conn.commit()

    # Show result page
    return render_template(
        "result.html",
        prediction=result,
        confidence=confidence
    )


# ===========================
# History Page
# ===========================
# ===========================
# History Page
# ===========================
@app.route("/history")
def history():

    search = request.args.get("search")

    if search:
        cursor.execute(
            "SELECT * FROM patient_predictions WHERE patient_name LIKE %s",
            ("%" + search + "%",)
        )
    else:
        cursor.execute(
            "SELECT * FROM patient_predictions ORDER BY id DESC"
        )

    data = cursor.fetchall()

    return render_template(
        "history.html",
        data=data,
        search=search
    )



# ===========================
# About Page
# ===========================
@app.route("/about")
def about():
    return render_template("about.html")


# ===========================
# Login Page
# ===========================
@app.route("/login")
def login():
    return render_template("login.html")
@app.route("/delete/<int:id>")
def delete(id):

    cursor.execute(
        "DELETE FROM patient_predictions WHERE id=%s",
        (id,)
    )

    conn.commit()

    return redirect("/history")

# ===========================
# Admin Page
# ===========================
@app.route("/admin")
def admin():
    return render_template("admin.html")
# ===========================
# Download PDF Report
# ===========================
@app.route("/download_pdf")
def download_pdf():

    cursor.execute("""
    SELECT
        patient_name,
        gender,
        age,
        bmi,
        hba1c,
        blood_glucose,
        prediction,
        confidence
    FROM patient_predictions
    ORDER BY id DESC
    LIMIT 1
    """)

    patient = cursor.fetchone()

    pdf_file = "Diabetes_Report.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    story = []

    story.append(Paragraph("<b><font size=18>GLUCOAI DIABETES REPORT</font></b>", styles["Title"]))
    story.append(Paragraph("<br/><br/>", styles["Normal"]))

    if patient:

        story.append(Paragraph(f"<b>Patient Name:</b> {patient[0]}", styles["Normal"]))
        story.append(Paragraph(f"<b>Gender:</b> {patient[1]}", styles["Normal"]))
        story.append(Paragraph(f"<b>Age:</b> {patient[2]}", styles["Normal"]))
        story.append(Paragraph(f"<b>BMI:</b> {patient[3]}", styles["Normal"]))
        story.append(Paragraph(f"<b>HbA1c Level:</b> {patient[4]}", styles["Normal"]))
        story.append(Paragraph(f"<b>Blood Glucose:</b> {patient[5]}", styles["Normal"]))
        story.append(Paragraph(f"<b>Prediction:</b> {patient[6]}", styles["Normal"]))
        story.append(Paragraph(f"<b>Confidence:</b> {patient[7]}%", styles["Normal"]))

        story.append(Paragraph("<br/><br/>", styles["Normal"]))

        if patient[6] == "Diabetic":

            story.append(Paragraph("<b>Diet Recommendation</b>", styles["Heading2"]))
            story.append(Paragraph("• Eat more vegetables and whole grains.", styles["Normal"]))
            story.append(Paragraph("• Avoid sugary drinks and processed food.", styles["Normal"]))
            story.append(Paragraph("• Walk at least 30 minutes daily.", styles["Normal"]))
            story.append(Paragraph("• Drink 2-3 liters of water.", styles["Normal"]))
            story.append(Paragraph("• Sleep 7-8 hours every day.", styles["Normal"]))

        else:

            story.append(Paragraph("<b>Healthy Lifestyle Tips</b>", styles["Heading2"]))
            story.append(Paragraph("• Continue a balanced diet.", styles["Normal"]))
            story.append(Paragraph("• Exercise regularly.", styles["Normal"]))
            story.append(Paragraph("• Maintain a healthy BMI.", styles["Normal"]))
            story.append(Paragraph("• Schedule regular health checkups.", styles["Normal"]))

        story.append(Paragraph("<br/><br/>", styles["Normal"]))

        story.append(Paragraph(
            "<b>Disclaimer:</b> This report is generated using a Machine Learning model "
            "for educational purposes only and should not replace professional medical advice.",
            styles["Normal"]
        ))

    doc.build(story)

    return send_file(
        pdf_file,
        as_attachment=True
    )
# ============================
# developer
# ===========================
@app.route("/developer")
def developer():
    return render_template("developer.html")
# ============================
# dashboard
# ===========================
# ===========================
# Dashboard
# ===========================
@app.route("/dashboard")
def dashboard():

    # Total Patients
    cursor.execute("SELECT COUNT(*) FROM patient_predictions")
    total = cursor.fetchone()[0]

    # Diabetic Patients
    cursor.execute("SELECT COUNT(*) FROM patient_predictions WHERE prediction='Diabetic'")
    diabetic = cursor.fetchone()[0]

    # Non-Diabetic Patients
    cursor.execute("SELECT COUNT(*) FROM patient_predictions WHERE prediction='Not Diabetic'")
    non_diabetic = cursor.fetchone()[0]

    # Average BMI
    cursor.execute("SELECT ROUND(AVG(bmi),2) FROM patient_predictions")
    avg_bmi = cursor.fetchone()[0] or 0

    # Average HbA1c
    cursor.execute("SELECT ROUND(AVG(hba1c),2) FROM patient_predictions")
    avg_hba1c = cursor.fetchone()[0] or 0

    return render_template(
        "dashboard.html",
        total=total,
        diabetic=diabetic,
        non_diabetic=non_diabetic,
        avg_bmi=avg_bmi,
        avg_hba1c=avg_hba1c
    )

# ===========================
# Run App
# ===========================
if __name__ == "__main__":
    app.run(debug=True)
