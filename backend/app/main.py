from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MongoDB 연결 설정 ===
MONGO_URL = "mongodb://localhost:27017"  # 로컬 MongoDB
client = AsyncIOMotorClient(MONGO_URL)
db = client["board_tutorial_db"]  # 사용할 데이터베이스 이름
posts_collection = db["posts"]    # 사용할 컬렉션 이름

# === Pydantic 모델 ===
class PostCreate(BaseModel):
    title: str
    content: str 
    author: str 

# MongoDB에서 가져온 문서를 변환하기 위한 모델
class PostResponse(PostCreate):
    id: str

@app.get("/")
def read_root():
    return {"message" : "Nice 2 meet U :)"}

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title="Custom Swagger",
        swagger_js_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.0/swagger-ui-bundle.js",  # 최신 JS
        swagger_css_url="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.0/swagger-ui.css",
    )

@app.post("/api/posts", response_model=PostResponse)
async def create_post(post_data: PostCreate):
    # MongoDB에 문서 삽입
    new_post = await posts_collection.insert_one(post_data.model_dump())
    
    # 삽입된 문서를 다시 조회
    created_post = await posts_collection.find_one({"_id": new_post.inserted_id})
    # ObjectId -> str 변환
    return PostResponse(
        id=str(created_post["_id"]),
        title=created_post["title"],
        content=created_post["content"],
        author=created_post["author"]
    )


@app.get("/api/posts", response_model=list[PostResponse])
async def get_posts():
    # MongoDB에서 모든 게시글 조회
    cursor = posts_collection.find()  # 비동기 커서
    posts = []
    async for doc in cursor:
        posts.append(PostResponse(
            id=str(doc["_id"]),
            title=doc["title"],
            content=doc["content"],
            author=doc["author"]
        ))
    return posts

@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: str):
    # id가 맞는 문서 하나 찾기
    post = await posts_collection.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostResponse(
        id=str(post["_id"]),
        title=post["title"],
        content=post["content"],
        author=post["author"]
    )

@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def update_post(post_id: str, post_data: PostCreate):
    # 업데이트 후 문서를 받아오기 위해 find_one_and_update 이용 가능
    updated_post = await posts_collection.find_one_and_update(
        {"_id": ObjectId(post_id)},
        {"$set": post_data.dict()},
        return_document=True
    )
    if not updated_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostResponse(
        id=str(updated_post["_id"]),
        title=updated_post["title"],
        content=updated_post["content"],
        author=updated_post["author"]
    )

@app.delete("/api/posts/{post_id}")
async def delete_post(post_id: str):
    result = await posts_collection.delete_one({"_id": ObjectId(post_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"message": "Post deleted successfully"}









