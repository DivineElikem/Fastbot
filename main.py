from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from model import call_chatmodel  # Importing the call_chatmodel function from model.py

app = FastAPI()

# Connect to SQLite database
conn = sqlite3.connect('sessions.db')
cursor = conn.cursor()

# Create sessions table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL UNIQUE
    )
''')
conn.commit()

# Create followups table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        user_message TEXT,
        ai_response TEXT,
        FOREIGN KEY(session_id) REFERENCES sessions(session_id)
    )
''')
conn.commit()

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # Insert or ignore session in sessions table
        cursor.execute('''
            INSERT OR IGNORE INTO sessions (session_id)
            VALUES (?)
        ''', (request.session_id,))
        conn.commit()

        # Retrieve chat history for the session
        cursor.execute('''
            SELECT user_message, ai_response FROM followups WHERE session_id=?
        ''', (request.session_id,))
        chat_history = cursor.fetchall()

        # Format chat history for the AI model
        messages = []
        for user_msg, ai_resp in chat_history:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "ai", "content": ai_resp})

        # Call the chat model
        response = await call_chatmodel(request.message, messages)
        
        # Insert user message and AI response into followups table
        cursor.execute('''
            INSERT INTO followups (session_id, user_message, ai_response)
            VALUES (?, ?, ?)
        ''', (request.session_id, request.message, response["response"]))
        conn.commit()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

    return {"response": response["response"], "messages": response["messages"]}

@app.get("/{session_id}/followups")
async def get_followups(session_id: str):
    try:
        # Retrieve follow-ups and AI responses for the session
        cursor.execute('''
            SELECT user_message, ai_response FROM followups WHERE session_id=?
        ''', (session_id,))
        followups = cursor.fetchall()
        if followups:
            return {
                "session_id": session_id,
                "followups": [{"user_message": f[0], "ai_response": f[1]} for f in followups]
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found.")
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/{session_id}/followups")
async def delete_followups(session_id: str):
    try:
        # Delete follow-ups for the session from followups table
        cursor.execute('''
            DELETE FROM followups WHERE session_id=?
        ''', (session_id,))
        conn.commit()
        return {"message": "Follow-ups deleted successfully."}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/{session_id}/followups/{followup_id}")
async def delete_followup(session_id: str, followup_id: int):
    try:
        # Delete specific follow-up from followups table
        cursor.execute('''
            DELETE FROM followups WHERE session_id=? AND id=?
        ''', (session_id, followup_id))
        conn.commit()
        return {"message": "Follow-up deleted successfully."}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
