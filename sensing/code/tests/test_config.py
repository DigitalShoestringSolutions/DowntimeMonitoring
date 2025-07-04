import json
import jsonschema
import os
try:
    import tomllib
except ImportError:
    import tomli as tomllib

def test_all_config():
    with open("./config_schema.json", "rb") as f:
        schema = json.load(f)
        for file in os.listdir("../config"):
            if file != "user_config.toml":
                assert do_config_test(f"../config/{file}",schema) == True

def do_config_test(file,schema):
    with open(file, "rb") as f:
        config = tomllib.load(f)
    try:
        jsonschema.validate(instance=config, schema=schema,
                            format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER)
        return True
    except jsonschema.ValidationError as v_err:
        print(f"CONFIG ERROR on {file} - {v_err.json_path} >> {v_err.message}")
        return False