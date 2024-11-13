from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from pymongo import MongoClient
from bson import ObjectId
import asyncio


app = FastAPI()

# 定義一個資料模型


class userList(BaseModel):
    name: Optional[str] = None  # name 是可選的
    idNumber: Optional[str] = None  # idNumber 是可選的
    healthMeasurement: Optional[int] = 0  # 默認為 0，但也可以不填
    healthEducation: Optional[int] = 0  # 默認為 0，但也可以不填
    exercise: Optional[int] = 0  # 默認為 0，但也可以不填

    class Config:
        # 設置 ORM 模式以便於處理 MongoDB 的 ObjectId
        json_encoders = {
            ObjectId: str
        }


# 資料庫
dbName = 'python'
collectionName = 'exercise'
client = MongoClient(
    "mongodb+srv://jmimiding4104:aaaa1111@cluster0.paad7v9.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
database = client[dbName]
collection = database[collectionName]

# 確認資料庫連結成功與否


async def connect_to_mongo():
    try:
        # 測試 ping 值，若沒有回應就會走 except 回報未連結
        await asyncio.to_thread(client.admin.command, 'ping')
        print("MongoDB 連接成功")
    except Exception as e:
        print(f"MongoDB 連接失敗: {e}")

# 開始時執行確認函式


@app.on_event("startup")
async def startup_event():
    await connect_to_mongo()
    
@app.post("/add_user/", response_model=userList)
async def add_user(user: userList):
    # 將 user 物件轉換成字典
    user_dict = user.dict(by_alias=True)
    # 插入資料到資料庫
    result = collection.insert_one(user_dict)
    # 將 MongoDB 回傳的 `_id` 設置到回傳的資料中
    user_dict["_id"] = str(result.inserted_id)
    return user_dict


# 比對是否有此人

@app.post("/count/")
async def matching_id(user: userList):
    print(user)
    idNumber = user.idNumber
    print(idNumber)
    result = collection.find_one({"idNumber": idNumber})
    if result:
        result['_id'] = str(result['_id'])  # 轉換 ObjectId
        return result
    else:
        raise HTTPException(status_code=404, detail="未找到符合的 ID")

# 取得所有 userList
@app.get("/count/", response_model=List[userList])
async def get_all_todos():
    todos = []
    for todo in collection.find():
        todo['_id'] = str(todo['_id'])
        todos.append(todo)

    return todos


# 建立新的 userList
@app.post("/todos/", response_model=userList)
async def create_todo(todo: userList):
    todo_dict = todo.dict()
    collection.insert_one(todo_dict)
    return todo


# 取得單一資料
@app.get("/todos/{id}", response_model=userList)
async def get_one_todos(id: str):
    todo_id = ObjectId(id)
    result = collection.find_one({"_id": todo_id})
    print(result)
    if result:
        result['_id'] = str(result['_id'])
        return result
    else:
        raise HTTPException(status_code=404, detail="未找到資料")

# 更新 ToDo


@app.put("/todos/{id}", response_model=userList)
async def update_todo(id: str, updatedTodo: userList):
    todo_id = ObjectId(id)
    result = collection.update_one(
        {"_id": todo_id},  # 查找條件
        {"$set": {"title": updatedTodo.title, "description": updatedTodo.description,
                  "completed": updatedTodo.completed}}
    )
    if result.matched_count > 0:
        updated_todo = await get_one_todos(id)
        return updated_todo
    else:
        raise HTTPException(status_code=404, detail="未找到資料")


# 刪除 ToDo
@app.delete("/todos/{id}", response_model=userList)
async def delete_todo(id: str):
    todo_id = ObjectId(id)
    result = collection.delete_one({"_id": todo_id})

    if result.deleted_count > 0:
        raise HTTPException(status_code=200, detail="刪除成功")
    else:
        raise HTTPException(status_code=404, detail="請確認 ID")
