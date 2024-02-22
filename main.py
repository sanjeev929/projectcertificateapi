import asyncpg
import smtplib
import random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import FastAPI, Request,Response
from asyncpg import exceptions
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Frame
from reportlab.pdfgen import canvas
from io import BytesIO

app = FastAPI()
current_date = datetime.date.today()
async def connect_to_db():
    return await asyncpg.connect(user="postgres", password="123",
                                 database="certificate", host="localhost")

def generate_covid_certificate(recipient_name, test_result, date, logo_filename, filename):
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = styles['Title']
    body_style = styles['BodyText']
    
    try:
        c.setFillColor(HexColor("#FFFFFF"))
        c.rect(0, 0, letter[0], letter[1], fill=True)
        c.drawImage("/home/ubuntu/projectcertificateapi/logo3.png", 210, 375, width=200, height=200, preserveAspectRatio=True)
        c.drawImage(logo_filename, 25, 700, width=75, height=75)
        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(HexColor("#1F497D"))
        c.drawString(125, 750, "COVID-19 Test Certificate")
        
        c.setFont("Helvetica", 12)
        c.drawString(125, 650, f"This is to certify that {recipient_name}")
        c.drawString(125, 635, "has been tested for COVID-19 on:")
        c.setFont("Helvetica-Bold", 14)
        c.drawString(125, 610, f"{date}")
        c.setFont("Helvetica", 12)
        c.drawString(125, 580, "This certificate is issued to confirm that the individual named above has undergone testing ")
        c.drawString(125, 565, "for COVID-19 on the specified date. The results of the test indicate the individual's")
        c.drawString(125, 550, "current health status with regard and should be presented as required.")
        
        if test_result.lower() == "positive":
            c.setFillColor(HexColor("#FF0000"))  # Red for positive
        else:
            c.setFillColor(HexColor("#008000"))  # Green for negative
        
        c.setFont("Helvetica-Bold", 14)
        c.drawString(125, 510, f"Test Result: {test_result.capitalize()}")
        c.setLineWidth(2)
        
        c.line(100, 200, 400, 200)
        c.setFont("Helvetica", 12)
        c.drawString(100, 180, "Authorized Signature")
        c.save()  # Uncomment this line if you want to save the PDF to a file
    except Exception as e:
        pass
    finally:
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
    return pdf_bytes

def generate_otp():
    return str(random.randint(100000, 999999))

async def send_email(email, otp):
    message = MIMEMultipart()
    message["From"] = "GOVT Verification COVID-19" 
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
        conn = await connect_to_db()
        email_exists = await check_email_exist(conn, email)
        if email_exists:
            await conn.close()
            return {"message":None,"error": True}
        otp = generate_otp()
        await send_email(email, otp)
        try:
            await conn.execute(
                "INSERT INTO users (name, email, phone, otp) VALUES ($1, $2, $3, $4)",
                name, email, phone, otp
            )
        except asyncpg.exceptions.UndefinedTableError:
            await conn.execute("""CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    email TEXT UNIQUE,
                    phone TEXT,
                    otp TEXT,
                    status TEXT,
                    issue_date DATE,
                    certificate BYTEA
                )""")
            await conn.execute(
                "INSERT INTO users (name, email, phone, otp) VALUES ($1, $2, $3, $4)",
                name, email, phone, otp
            )

        await conn.close()

        return {"message": "Data received successfully","error":False}
    except Exception as e:
        return {"message":None,"error": "An error occurred while processing the request"}
    
@app.post("/otpgenerate/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        conn = await connect_to_db()
        email_exists = await check_email_exist(conn, email)
        if not email_exists:
            await conn.close()
            return {"name":None,"error":"Email not exists"}
        try:
            new_otp = generate_otp()
            await conn.execute(
                "UPDATE users SET otp = $1 WHERE email = $2",
                new_otp, email
            )
            current_name = await conn.fetchval(
                "SELECT name FROM users WHERE email = $1",
                email
            )
            await conn.close()
            await send_email(email, new_otp)
            return {"name":current_name,"error":None}
        
        except Exception as e:
            return {"name":None,"error":str(e)}
    except Exception as e:
        return {"name":None,"error":str(e)}
    
@app.post("/otpverify/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        otp = data.get("otp")
        conn = await connect_to_db()
        email_exists = await check_email_exist(conn, email)
        if not email_exists:
            await conn.close()
            return {"name":None,"error":"Email not exists"}
        try:
        
            current_otp = await conn.fetchval(
            "SELECT otp FROM users WHERE email = $1",
            email
                )
            current_name = await conn.fetchval(
            "SELECT name FROM users WHERE email = $1",
            email
                )
            await conn.close()
            if int(current_otp) == int(otp):

                return {"otp status":True,"name":current_name}
            else:
                return {"otp status":False,"name":current_name}
        except Exception as e:
            return {"error":str(e)}
    except Exception as e:
        return {"error":str(e)}    

@app.get("/getall/")
async def get_all_users():
    try:
        conn = await connect_to_db()
        query = "SELECT name, email, phone, status FROM users"
        users = await conn.fetch(query)
        await conn.close()
        if users:
            return users
        else:
            return {"message": "No users found"}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/login/")
async def register_admin(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    try:
        conn = await connect_to_db()
        query = "SELECT * FROM admins WHERE email = $1 AND password = $2"
        admin = await conn.fetchrow(query, email, password)
        await conn.close()
        if admin:
            return {"state": True,"error": None}
        else:
            return {"state":False,"error": "Invalid credentials"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/admin_registration/")
async def register_admin(request: Request):
    data = await request.json()
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    try:
        conn = await connect_to_db()
        # Check if the table exists, create it if not
        try:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS admins (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100),
                    password VARCHAR(100)
                )
                """
            )
        except exceptions.PostgresError as e:
            return {"error": str(e)}

        # Insert admin data into the table
        try:
            await conn.execute(
                """
                INSERT INTO admins (name, email, password) VALUES ($1, $2, $3)
                """,
                name, email, password
            )
        except exceptions.PostgresError as e:
            return {"error": str(e)}

        await conn.close()
        return {"state": True}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/adminchange/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        status = data.get("status")
        conn = await connect_to_db()
        try:
            await conn.execute(
                "UPDATE users SET status = $1, issue_date = $2  WHERE email = $3",
                status, current_date, email
            )
            current_user = await conn.fetchrow(
                "SELECT name, status, issue_date FROM users WHERE email = $1",
                email
            )
            if current_user[1] =='true':
                status = 'positive'
            else:
                status ='negative'     
            logo_filename = "/home/ubuntu/projectcertificateapi/logo3.png"
            certificate=generate_covid_certificate(current_user[0], status, current_user[2], logo_filename,'covid_certificate.pdf')
            await conn.execute(
                "UPDATE users SET certificate = $1 WHERE email = $2",
                certificate, email
            )
            await conn.close()
            return "successfully update state"
        
        except Exception as e:
            return {"name":None,"error":str(e)}
    except Exception as e:
        return {"name":None,"error":str(e)}


@app.post("/downloadcertificate/")
async def submit_data1(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        conn = await connect_to_db()
        try:
            certificate = await conn.fetchval(
            "SELECT certificate FROM users WHERE email = $1",
            email
                )
            await conn.close()
            return Response(content=certificate, media_type="application/octet-stream")
        except Exception as e:
            return {"name": None, "error": str(e)}
    except Exception as e:
        return {"name": None, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
