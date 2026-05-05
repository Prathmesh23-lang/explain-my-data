# -------------------------
# ENV + OPENAI SETUP
# -------------------------
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -------------------------
# FIX MATPLOTLIB (NO GUI)
# -------------------------
import matplotlib
matplotlib.use("Agg")


# -------------------------
# IMPORTS
# -------------------------
from fastapi import FastAPI, UploadFile, File
from database import SessionLocal
from models import User, Dataset, AnalysisResult

import pandas as pd
import random


app = FastAPI()


# -------------------------
# HOME
# -------------------------
@app.get("/")
def home():
    return {"message": "Backend is running"}


# -------------------------
# TEST DB
# -------------------------
@app.get("/test-db")
def test_db():
    db = SessionLocal()
    try:
        new_user = User(
            email=f"test{random.randint(1,10000)}@example.com",
            password_hash="test123"
        )

        db.add(new_user)
        db.commit()

        return {"message": "User inserted"}

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()


# -------------------------
# UPLOAD FILE
# -------------------------
@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    UPLOAD_FOLDER = "uploads"
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_path = f"{UPLOAD_FOLDER}/{file.filename}"

    # Save file
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    df = pd.read_csv(file_path)

    db = SessionLocal()
    try:
        dataset = Dataset(
            user_id=None,
            filename=file.filename,
            file_path=file_path,
            row_count=len(df),
            col_count=len(df.columns)
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        return {
            "message": "File uploaded & saved",
            "dataset_id": str(dataset.id),
            "rows": len(df),
            "columns": len(df.columns),
            "columns_list": list(df.columns)
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()


# -------------------------
# CLEAN NaN FOR JSON
# -------------------------
def clean_nan(obj):
    import math

    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    else:
        return obj


# -------------------------
# ANALYZE DATA
# -------------------------
@app.get("/analyze/{dataset_id}")
def analyze_data(dataset_id: str):
    import matplotlib.pyplot as plt

    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            return {"error": "Dataset not found"}

        df = pd.read_csv(dataset.file_path)

        # PROFILE
        profile = {
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "summary": df.describe(include="all").to_dict()
        }

        profile = clean_nan(profile)

        # INSIGHTS
        insights = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                insights.append(f"{col} average is {df[col].mean()}")

            if df[col].isnull().sum() > 0:
                insights.append(f"{col} has missing values")

        # CHART
        os.makedirs("charts", exist_ok=True)
        chart_path = f"charts/{dataset_id}.png"

        df.hist()
        plt.savefig(chart_path)
        plt.close()

        # SAVE RESULT
        result = AnalysisResult(
            dataset_id=dataset.id,
            profile_json=profile,
            charts_json={"histogram": chart_path},
            insights_json=insights
        )

        db.add(result)
        db.commit()

        return {
            "profile": profile,
            "insights": insights,
            "chart": chart_path
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()


# -------------------------
# AI QUESTION ANSWERING
# -------------------------
@app.get("/ask/{dataset_id}")
def ask_ai(dataset_id: str, question: str):
    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

        if not dataset:
            return {"error": "Dataset not found"}

        df = pd.read_csv(dataset.file_path)

        preview = df.head(20).to_string()

        prompt = f"""
You are a data analyst.

Dataset preview:
{preview}

User question:
{question}

Answer clearly and concisely.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful data analyst."},
                {"role": "user", "content": prompt}
            ]
        )

        answer = response.choices[0].message.content

        return {"answer": answer}

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()