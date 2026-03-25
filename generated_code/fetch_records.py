from fastapi import FastAPI

def main():
    app = FastAPI()
    @app.get("/records")
    def read_records():
        return RequestLog.query().all()