import asyncpg
import smtplib
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import FastAPI, Request

app = FastAPI()

async def connect_to_db():
    return await asyncpg.connect(user="postgres", password="123",
                                 database="certificate", host="localhost")

def generate_otp():
    return str(random.randint(100000, 999999))

async def send_email(email, otp):
    message = MIMEMultipart()
    message["From"] = "GOVT Verification COVID-19"  # Sender's email address
    message["To"] = email
    message["Subject"] = "OTP for Verification"
    body = f"Your OTP is: {otp}"
    message.attach(MIMEText(body, "plain"))

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login("sanjeevsanju929@gmail.com", "fhge kait cnqe mjba")
    s.sendmail("sanjeevsanju929@gmail.com", email, message.as_string())
    s.quit()

async def check_email_exist(conn, email):
    try:
        query = "SELECT COUNT(*) FROM users WHERE email = $1"
        result = await conn.fetchval(query, email)
        return result > 0
    except:
        return False

@app.post("/submit-data/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")

        # Connect to the database
        conn = await connect_to_db()

        # Check if email already exists
        email_exists = await check_email_exist(conn, email)
        if email_exists:
            await conn.close()
            return {"error": "Email already exists"}

        # Generate OTP
        otp = generate_otp()

        # Send email with OTP
        await send_email(email, otp)

        # Insert data into the database
        try:
            await conn.execute(
                "INSERT INTO users (name, email, phone, otp) VALUES ($1, $2, $3, $4)",
                name, email, phone, otp
            )
        except asyncpg.exceptions.UndefinedTableError:
            # If the table doesn't exist, create it and then insert data
            await conn.execute("""CREATE TABLE IF NOT EXISTS users (
                                    id SERIAL PRIMARY KEY,
                                    name TEXT,
                                    email TEXT UNIQUE,
                                    phone TEXT,
                                    otp TEXT,
                                    status TEXT,
                                    issue_date DATE
                                )""")
            await conn.execute(
                "INSERT INTO users (name, email, phone, otp) VALUES ($1, $2, $3, $4)",
                name, email, phone, otp
            )

        # Close the database connection
        await conn.close()

        return {"message": "Data received successfully"}
    except Exception as e:
        print("An error occurred:", str(e))
        return {"error": "An error occurred while processing the request"}
    
@app.post("/otpgenerate/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        email = data.get("email")

        # Connect to the database
        conn = await connect_to_db()

        # Check if email already exists
        email_exists = await check_email_exist(conn, email)
        if not email_exists:
            await conn.close()
            return {"error": "Email not exists"}

        try:
            # Connect to the database
            conn = await connect_to_db()

            # Check if email already exists
            email_exists = await check_email_exist(conn, email)
            if not email_exists:
                await conn.close()
                return {"error": "Email does not exist"}

            # Generate a new OTP
            new_otp = generate_otp()

            # Update the OTP for the specified email
            await conn.execute(
                "UPDATE users SET otp = $1 WHERE email = $2",
                new_otp, email
            )

            # Close the database connection
            await conn.close()

            # Send email with the new OTP
            await send_email(email, new_otp)

            return {"message": "OTP updated and sent successfully"}
        except Exception as e:
            print("An error occurred:", str(e))
            return {"error": "An error occurred while processing the request"} 
    except Exception as e:
        print("An error occurred:", str(e))
        return {"error": "An error occurred while processing the request"}    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
