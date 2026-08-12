import asyncio
import json
from typing import Any, Dict, List

import aiohttp


class IndevoltAPI:
    """Handles all HTTP communication with Indevolt devices"""
    
    def __init__(self, host: str, port: int, session: aiohttp.ClientSession):
        self.host = host
        self.port = port
        self.session = session
        self.base_url = f"http://{host}:{port}/rpc"
        self.timeout = aiohttp.ClientTimeout(total=60)
    
    async def fetch_data(self, keys: List[int]) -> Dict[str, Any]:
        """Fetch raw JSON data from the device"""
        config_param = json.dumps({"t": keys}).replace(" ", "")
        url = f"{self.base_url}/Indevolt.GetData?config={config_param}"
        
        try:
            async with self.session.post(url, timeout=self.timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP status error: {response.status}")
                return await response.json()
                
        except asyncio.TimeoutError:
            raise Exception("Indevolt.GetData Request timed out")
        except aiohttp.ClientError as err:
            raise Exception(f"Indevolt.GetData Network error: {err}")
        
    async def set_data(
        self,
        point: int,
        value: List[int],
    ) -> bool:
        """Send configuration data to the device"""
        config_param = json.dumps({"f": 16,"t": point,"v": value}).replace(" ", "")
        url = f"{self.base_url}/Indevolt.SetData?config={config_param}"

        try:
            async with self.session.post(url, timeout=self.timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP status error: {response.status}")
                data = await response.json()
                return bool(data.get("result", False))

        except asyncio.TimeoutError:
            raise Exception("Indevolt.SetData Request timed out")
        except aiohttp.ClientError as err:
            raise Exception(f"Indevolt.SetData Network error: {err}")

    async def get_config(self) -> Dict[str, Any]:
        url = f"{self.base_url}/Sys.GetConfig"

        try:
            async with self.session.get(url=url, timeout=self.timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP status error: {response.status}")
                return await response.json()
            
        except asyncio.TimeoutError:
            raise Exception("Indevolt Sys.GetConfig Request timed out")
        except aiohttp.ClientError as err:
            raise Exception(f"Indevolt Sys.GetConfig Network error: {err}")
