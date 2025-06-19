from django.conf import settings

def get_collection(name, db="skill_based"):
    return settings.MONGO_CLIENT[db][name]
