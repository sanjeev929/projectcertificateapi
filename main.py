import smtplib, random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import FastAPI, Request

app = FastAPI()
def generate_otp():
    return str(random.randint(100000, 999999))

@app.post("/submit-data/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        print(name, email, phone)

        # Generate OTP
        otp = generate_otp()

        # Create a multipart message
        message = MIMEMultipart()
        message["From"] = "GOVT Verfication COVID-19"  # Sender's email address
        message["To"] = email
        message["Subject"] = "OTP for Verification"

        # Add body to the email
        body = f"Your OTP is: {otp}"
        message.attach(MIMEText(body, "plain"))

        # Establish SMTP connection
        s = smtplib.SMTP('smtp.gmail.com', 587)
        s.starttls()
        s.login("sanjeevsanju929@gmail.com", "fhge kait cnqe mjba")

        # Send email
        s.sendmail("sanjeevsanju929@gmail.com", email, message.as_string())
        s.quit()

        print("Email sent successfully to:", email)

        # Return a response indicating success
        return {"message": "Data received successfully"}
    except Exception as e:
        print("An error occurred:", str(e))
        return {"error": "An error occurred while processing the request"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
