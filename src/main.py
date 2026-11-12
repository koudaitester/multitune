from fastapi import FastAPI
from domains.tune_domain.api import router as tune_router
from domains.good_domain.api import router as good_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Tune 活体视觉评估服务")
app.include_router(tune_router, prefix="/api/v1")
app.include_router(good_router, prefix="/api/v1")

app.mount("/html_basic", StaticFiles(directory="html_basic"), name="html_static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
