def handle_schema_memory(payload, db):
    command = payload.get("command")
    collection_name = payload.get("collection")
    collection = db[collection_name]

    if command == "create":
        data = payload.get("data", {})
        result = collection.insert_one(data)
        return {"status": "created", "inserted_id": str(result.inserted_id)}

    elif command == "read":
        query = payload.get("filter", {})
        results = list(collection.find(query, {"_id": 0}))
        return results

    elif command == "update":
        query = payload.get("filter", {})
        update = {"$set": payload.get("update", {})}
        result = collection.update_many(query, update)
        return {"status": "updated", "modified_count": result.modified_count}

    elif command == "delete":
        query = payload.get("filter", {})
        result = collection.delete_many(query)
        return {"status": "deleted", "deleted_count": result.deleted_count}

    else:
        return {"error": "Unknown command"}
