import random

from curl_cffi.requests import AsyncSession


class Client:
    def __init__(self, proxy=None, timeout=15, verify=True, impersonate='safari15_3'):
        self.proxies = {"http": proxy, "https": proxy}
        self.timeout = timeout
        self.verify = verify

        self.impersonate = impersonate
        # impersonate=self.impersonate

        # self.ja3 = ""
        # self.akamai = ""
        # ja3=self.ja3, akamai=self.akamai
        self.session = AsyncSession(proxies=self.proxies, timeout=self.timeout, impersonate=self.impersonate, verify=self.verify)
        self.session2 = AsyncSession(proxies=self.proxies, timeout=self.timeout, impersonate=self.impersonate, verify=self.verify)

    async def post(self, *args, **kwargs):
        r = await self.session.post(*args, **kwargs)
        return r

    async def post_stream(self, *args, headers=None, cookies=None, **kwargs):
        if self.session:
            headers = headers or self.session.headers
            cookies = cookies or self.session.cookies
        r = await self.session2.post(*args, headers=headers, cookies=cookies, **kwargs)
        return r

    async def get(self, *args, **kwargs):
        r = await self.session.get(*args, **kwargs)
        return r

    async def request(self, *args, **kwargs):
        r = await self.session.request(*args, **kwargs)
        return r

    async def put(self, *args, **kwargs):
        r = await self.session.put(*args, **kwargs)
        return r

    async def close(self):
        if self.session:
            try:
                await self.session.close()
                del self.session
            except Exception:
                pass
        if self.session2:
            try:
                await self.session2.close()
                del self.session2
            except Exception:
                pass
