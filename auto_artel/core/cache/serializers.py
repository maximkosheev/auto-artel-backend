import json


class JsonCacheSerializer:
    def dumps(self, value):
        return json.dumps(value, ensure_ascii=False).encode("utf-8")

    def loads(self, bytes_value):
        if bytes_value is None:
            return None
        return json.loads(bytes_value.decode("utf-8"))
