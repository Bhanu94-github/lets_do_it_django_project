import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
instructor_db = client["instructor"]
results_collection = instructor_db["results"]

def get_all_questions(skill, difficulty):
    skill = skill.lower()
    db = client["skill_based"]
    if skill in db.list_collection_names():
        return list(db[skill].find({"difficulty": difficulty}))
    return []

def save_result(result_data):
    results_collection.insert_one(result_data)
