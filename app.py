import types

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.background import BackgroundTask

from chatgpt.ChatService import ChatService
from chatgpt.reverseProxy import chatgpt_reverse_proxy
from utils.Logger import Logger
from utils.authorization import verify_token
from utils.config import api_prefix
from utils.retry import async_retry

import warnings

warnings.filterwarnings("ignore")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def to_send_conversation(request_data, access_token):
    chat_service = ChatService(access_token)
    await chat_service.set_dynamic_data(request_data)
    try:
        await chat_service.get_chat_requirements()
        return chat_service
    except HTTPException as e:
        await chat_service.close_client()
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.post(f"/{api_prefix}/v1/chat/completions" if api_prefix else "/v1/chat/completions")
async def send_conversation(request: Request, token=Depends(verify_token)):
    try:
        request_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail={"error": "Invalid JSON body"})

    chat_service = await async_retry(to_send_conversation, request_data, token)
    try:
        await chat_service.prepare_send_conversation()
        res = await chat_service.send_conversation()
        if isinstance(res, types.AsyncGeneratorType):
            background = BackgroundTask(chat_service.close_client)
            return StreamingResponse(res, media_type="text/event-stream", background=background)
        else:
            background = BackgroundTask(chat_service.close_client)
            return JSONResponse(res, media_type="application/json", background=background)
    except HTTPException as e:
        await chat_service.close_client()
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        await chat_service.close_client()
        Logger.error(f"Server error, {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def reverse_proxy(request: Request, path: str):
    return await chatgpt_reverse_proxy(request, path)


if __name__ == "__main__":
    import uvicorn

    log_config = uvicorn.config.LOGGING_CONFIG
    default_format = "%(asctime)s | %(levelname)s | %(message)s"
    access_format = r'%(asctime)s | %(levelname)s | %(client_addr)s: %(request_line)s %(status_code)s'
    log_config["formatters"]["default"]["fmt"] = default_format
    log_config["formatters"]["access"]["fmt"] = access_format

    uvicorn.run("app:app", host="0.0.0.0", port=5005)
