from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import boto3
import os
import openai
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

# Initialize FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS S3 Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

# OpenAI Configuration
openai.api_key = os.getenv("OPENAI_API_KEY")

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting message: {e}")

manager = ConnectionManager()

# LangChain Integration
chat_model = ChatOpenAI(model_name="gpt-4")
prompt_template = ChatPromptTemplate.from_template(
    "Evaluate the findings in the following report:\n{report_text}\n\nProvide a detailed analysis."
)
llm_chain = LLMChain(llm=chat_model, prompt=prompt_template)

async def fetch_s3_file(bucket: str, key: str) -> str:
    """Fetch a file from S3."""
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response["Body"].read().decode("utf-8")
        return content
    except Exception as e:
        return f"Error fetching file from S3: {e}"

@app.websocket("/ws/llm-agent")
async def llm_agent_websocket(websocket: WebSocket):
    """WebSocket endpoint to interact with LLM and evaluate findings."""
    await manager.connect(websocket)
    try:
        while True:
            # Receive user input
            user_input = await websocket.receive_text()

            if user_input.lower() == "exit":
                break

            if user_input.startswith("fetch:"):
                # Extract the S3 key from user input
                s3_key = user_input.replace("fetch:", "").strip()
                report_text = await fetch_s3_file(S3_BUCKET_NAME, s3_key)

                if report_text.startswith("Error"):
                    await websocket.send_text(report_text)
                else:
                    # Query the LLM with the findings report
                    analysis = llm_chain.run(report_text=report_text)
                    await websocket.send_text(analysis)
            else:
                await websocket.send_text("Unknown command. Use 'fetch:<S3_KEY>' to analyze a report.")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)