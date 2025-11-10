from fastapi import FastAPI


app = FastAPI() 

@app.get("/")
def read_root():
    return {"message": "HelloWorld"}

@app.get("/message")
def read_message():
    return {"message": "正常に動作しています"}