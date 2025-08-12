import uvicorn

def main():
    """Run the API server"""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    main()
