from litellm import acompletion, exceptions
from litellm.utils import completion_cost
from app.config import yaml_config

async def execute_llm_call(model_name: str, prompt: str):
    fallbacks = yaml_config.get("fallbacks", [])
    backup_model = None
    for f in fallbacks:
        if f.get("primary") == model_name:
            backup_model = f.get("backup")
            break
            
    try:
        response = await acompletion(model=model_name, messages=[{"role": "user", "content": prompt}])
        try:
            cost = completion_cost(completion_response=response, model=model_name)
        except Exception:
            cost = 0.0
        return response, model_name, cost
    except (exceptions.RateLimitError, exceptions.APIConnectionError, exceptions.BadRequestError) as e:
        if backup_model:
            print(f"Primary model {model_name} failed. Falling back to {backup_model}")
            response = await acompletion(model=backup_model, messages=[{"role": "user", "content": prompt}])
            try:
                cost = completion_cost(completion_response=response, model=backup_model)
            except Exception:
                cost = 0.0
            return response, backup_model, cost
        else:
            raise e
