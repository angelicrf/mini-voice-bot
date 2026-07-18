from fastapi import FastAPI

app = FastAPI()

@app.get("/voice")
def voice():

    return {
        "response":
        "Hello from Voice AI!"
    }