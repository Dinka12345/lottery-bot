from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_balances = {12345678: 100.0}
p2p_ads = [
    {
        "id": 1,
        "seller_id": 999,
        "seller_name": "EthiopiaXchange",
        "type": "SELL",
        "payment": "CBE",
        "price": 140.5,
        "total_amount": 50.0,
        "min_limit": 5.0,
        "max_limit": 50.0,
        "acc_num": "100012345678",
        "acc_name": "Abebe B."
    }
]

class CreateAdRequest(BaseModel):
    user_id: int
    type: str
    payment: str
    price: float
    total_amount: float
    min_limit: float
    max_limit: float
    acc_num: str
    acc_name: str

@app.get("/api/marketplace")
def get_marketplace():
    return {"ads": p2p_ads}

@app.get("/api/wallet/{user_id}")
def get_wallet(user_id: int):
    balance = user_balances.get(user_id, 0.0)
    return {"user_id": user_id, "usdt_balance": balance}

@app.post("/api/ads/create")
def create_ad(ad: CreateAdRequest):
    new_id = len(p2p_ads) + 1
    new_ad = ad.model_dump() if hasattr(ad, 'model_dump') else ad.dict()
    new_ad["id"] = new_id
    p2p_ads.append(new_ad)
    return {"status": "success", "ad": new_ad}

