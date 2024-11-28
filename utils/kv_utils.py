def set_value_for_key(data, target_key, new_value):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                data[key] = new_value
            else:
                set_value_for_key(value, target_key, new_value)
    elif isinstance(data, list):
        for item in data:
            set_value_for_key(item, target_key, new_value)
