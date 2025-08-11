root@ubuntu-s-1vcpu-2gb-nyc1-01:~# python3 -c "import redis; print('✅ Redis package installed successfully')"
✅ Redis package installed successfully
root@ubuntu-s-1vcpu-2gb-nyc1-01:~# mkdir -p /root/infrastructure/cache
root@ubuntu-s-1vcpu-2gb-nyc1-01:~# mkdir -p /root/infrastructure/services
root@ubuntu-s-1vcpu-2gb-nyc1-01:~# ls -la /root/config/
total 24
drwxr-xr-x 3 root root 4096 Feb 28 02:48 .
drwx------ 8 root root 4096 Aug 10 23:56 ..
drwxr-xr-x 2 root root 4096 Feb 28 02:48 __pycache__
-rw-r--r-- 1 root root 3678 Feb 22 22:49 settings.py
-rw-r--r-- 1 root root 5807 Feb 28 02:48 strat_settings.py
root@ubuntu-s-1vcpu-2gb-nyc1-01:~# head -20 /root/MA_Unified_Strat.py
import pandas as pd
from config.settings import MONGO_CONNECTION_STRING
from pymongo import MongoClient
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional
from config.strat_settings import STRATEGIES

# Set up database connections
client = MongoClient(
    MONGO_CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True
)
price_db = client["streamed_prices"]
signals_db = client["signals"]

# Logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
root@ubuntu-s-1vcpu-2gb-nyc1-01:~# grep -n "async_notification" /root/MA_Unified_Strat.py
root@ubuntu-s-1vcpu-2gb-nyc1-01:~# 

