from pymongo import MongoClient

class MongoDb:
    def __init__(self, uri, database):
        self.__client__ = MongoClient(uri)
        self.__database__ = self.__client__[database]
    
    def get_document(self, collection, filter: dict):
        collection = self.__database__[collection]
        response = collection.find(filter)

        result = []

        for doc in response:
            result.append(doc)

        if len(result) == 1:
            return result[0]

        return result

    def update_document(self, collection: str, filter: dict, query: dict):
        collection = self.__database__[collection]
        response = collection.update_many(filter, query)
        return response.modified_count

    def replace_document(self, collection, filter, new_doc):
        result = self.__database__[collection].replace_one(filter, new_doc)
        return result.modified_count
