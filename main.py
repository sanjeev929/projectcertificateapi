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
                    issue_date DATE,
                    certificate BYTEA
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
            print(current_name)
            await conn.close()

            # Send email with the new OTP
            await send_email(email, new_otp)
            print(current_name)
            return {"name":current_name,"error":None}
        
        except Exception as e:
            print("An error occurred:", str(e))
            return {"name":None,"error":str(e)}
    except Exception as e:
        print("An error occurred:", str(e))
        return {"name":None,"error":str(e)}
    
@app.post("/otpverify/")
async def submit_data(request: Request):
    try:
        data = await request.json()
        email = data.get("email")
        otp = data.get("otp")
        print(email)
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
            print(type(current_otp),type(otp),current_name)
            if int(current_otp) == int(otp):

                return {"otp status":True,"name":current_name}
            else:
                return {"otp status":False,"name":current_name}
        except Exception as e:
            print("An error occurred:", str(e))
            return {"error":str(e)}
    except Exception as e:
        print("An error occurred:", str(e))
        return {"error":str(e)}    

@app.get("/getall/")
async def get_all_users():
    try:
        conn = await connect_to_db()
        
        # Fetch all users from the database
        query = "SELECT name, email, phone, state FROM users"
        users = await conn.fetch(query)
        
        # Close the database connection
        await conn.close()
        print(users)
        # Return the list of users
        return {"users": users}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
