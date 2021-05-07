import json

def save_json_file(json_content_object, file_location):
    # fail-safe when JSON-serialization fails
    file_string = json.dumps(json_content_object, default=lambda o: o.__dict__, ensure_ascii=False, indent=4)
    with open(file_location, 'w', encoding='utf-8') as json_file:
        json_file.write(file_string + '\n')

def load_json_file(file_location):
    data = dict()
    with open(file_location) as json_file:
        data = json.load(json_file)
    return data
