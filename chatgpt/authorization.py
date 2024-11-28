import asyncio
import json
import random
import uuid

import ua_generator
from ua_generator.options import Options
from ua_generator.data.version import VersionRange
from fastapi import HTTPException

import utils.configs as configs
import utils.globals as globals
from chatgpt.refreshToken import rt2ac
from utils.Logger import logger


def get_req_token(req_token, seed=None):
    if configs.auto_seed:
        available_token_list = list(set(globals.token_list) - set(globals.error_token_list))
        length = len(available_token_list)
        if seed and length > 0:
            if seed not in globals.seed_map.keys():
                globals.seed_map[seed] = {"token": random.choice(available_token_list), "conversations": []}
                with open(globals.SEED_MAP_FILE, "w") as f:
                    json.dump(globals.seed_map, f, indent=4)
            else:
                req_token = globals.seed_map[seed]["token"]
            return req_token

        if req_token in configs.authorization_list:
            if len(available_token_list) > 0:
                if configs.random_token:
                    req_token = random.choice(available_token_list)
                    return req_token
                else:
                    globals.count += 1
                    globals.count %= length
                    return available_token_list[globals.count]
            else:
                return None
        else:
            return req_token
    else:
        seed = req_token
        if seed not in globals.seed_map.keys():
            raise HTTPException(status_code=401, detail={"error": "Invalid Seed"})
        return globals.seed_map[seed]["token"]


def get_fp(req_token):
    fp = globals.fp_map.get(req_token, {})
    if fp and fp.get("user-agent") and fp.get("impersonate"):
        if "proxy_url" in fp.keys() and fp["proxy_url"] is None and fp["proxy_url"] not in configs.proxy_url_list:
            fp["proxy_url"] = random.choice(configs.proxy_url_list) if configs.proxy_url_list else None
            globals.fp_map[req_token] = fp
            with open(globals.FP_FILE, "w", encoding="utf-8") as f:
                json.dump(globals.fp_map, f, indent=4)
        if globals.impersonate_list and "impersonate" in fp.keys() and fp["impersonate"] not in globals.impersonate_list:
            fp["impersonate"] = random.choice(globals.impersonate_list)
            globals.fp_map[req_token] = fp
            with open(globals.FP_FILE, "w", encoding="utf-8") as f:
                json.dump(globals.fp_map, f, indent=4)
        if configs.user_agents_list and "user-agent" in fp.keys() and fp["user-agent"] not in configs.user_agents_list:
            fp["user-agent"] = random.choice(configs.user_agents_list)
            globals.fp_map[req_token] = fp
            with open(globals.FP_FILE, "w", encoding="utf-8") as f:
                json.dump(globals.fp_map, f, indent=4)
        fp = {k.lower(): v for k, v in fp.items()}
        return fp
    else:
        options = Options(version_ranges={
            'chrome': VersionRange(min_version=124),
            'edge': VersionRange(min_version=124),
        })
        ua = ua_generator.generate(device='desktop', browser=('chrome', 'edge', 'firefox', 'safari'),
                                   platform=('windows', 'macos'), options=options)
        fp = {
            "user-agent": ua.text if not configs.user_agents_list else random.choice(configs.user_agents_list),
            "sec-ch-ua-platform": ua.ch.platform,
            "sec-ch-ua": ua.ch.brands,
            "sec-ch-ua-mobile": ua.ch.mobile,
            "impersonate": random.choice(globals.impersonate_list),
            "proxy_url": random.choice(configs.proxy_url_list) if configs.proxy_url_list else None,
            "oai-device-id": str(uuid.uuid4())
        }
        if not req_token:
            return fp
        else:
            globals.fp_map[req_token] = fp
            with open(globals.FP_FILE, "w", encoding="utf-8") as f:
                json.dump(globals.fp_map, f, indent=4)
            return fp


async def verify_token(req_token):
    if not req_token:
        if configs.authorization_list:
            logger.error("Unauthorized with empty token.")
            raise HTTPException(status_code=401)
        else:
            return None
    else:
        if req_token.startswith("eyJhbGciOi") or req_token.startswith("fk-"):
            access_token = req_token
            return access_token
        elif len(req_token) == 45:
            try:
                if req_token in globals.error_token_list:
                    raise HTTPException(status_code=401, detail="Error RefreshToken")

                access_token = await rt2ac(req_token, force_refresh=False)
                return access_token
            except HTTPException as e:
                raise HTTPException(status_code=e.status_code, detail=e.detail)
        else:
            return req_token


async def refresh_all_tokens(force_refresh=False):
    for token in list(set(globals.token_list) - set(globals.error_token_list)):
        if len(token) == 45:
            try:
                await asyncio.sleep(0.5)
                await rt2ac(token, force_refresh=force_refresh)
            except HTTPException:
                pass
    logger.info("All tokens refreshed.")
