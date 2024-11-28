import json

from fastapi import Request
from fastapi.responses import Response

from app import app
from gateway.reverseProxy import chatgpt_reverse_proxy
from utils.kv_utils import set_value_for_key


@app.post("/v1/initialize")
async def initialize(request: Request):
    initialize_response = (await chatgpt_reverse_proxy(request, f"/v1/initialize"))
    initialize_str = initialize_response.body.decode('utf-8')
    initialize_json = json.loads(initialize_str)
    set_value_for_key(initialize_json, "ip", "8.8.8.8")
    set_value_for_key(initialize_json, "country", "US")
    return Response(content=json.dumps(initialize_json, indent=4), media_type="application/json")


@app.post("/v1/rgstr")
async def rgstr():
    return Response(status_code=202, content=json.dumps({"success": True}, indent=4), media_type="application/json")


@app.post("/ces/v1/{path:path}")
async def ces_v1():
    return Response(status_code=202, content=json.dumps({"success": True}, indent=4), media_type="application/json")
