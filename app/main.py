from fastapi import FastAPI

app = FastAPI(
    title="E-commerce Repricing Engine",
    description=(
        "Rule-based competitive pricing engine for ecommerce products."
    ),
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "name": "E-commerce Repricing Engine",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}