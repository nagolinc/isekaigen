import requests
import json
import os

# Set your OpenRouter API key and other optional parameters
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
YOUR_SITE_URL = "your_site_url_here"  # Optional, for rankings
YOUR_APP_NAME = "your_app_name_here"  # Optional, for rankings


def chat(
    input_text,
    system_prompt="do your best",
    history=None,
    json_mode=False,
    max_history=8,
    verbose=False,
):

    if history is None:
        history = [{"role": "system", "content": system_prompt}]
    else:
        # make sure we override system prompt (it is the content of the first message)
        history[0] = {"role": "system", "content": system_prompt}

    if len(history) > max_history:
        history = history[:1] + history[-max_history:]
    messages = history + [{"role": "user", "content": input_text}]

    if verbose:
        print("\n\nMESSAGES: >>>", messages)

    # Set the response format according to the json_mode
    response_format = {"type": "json_object"} if json_mode else {"type": "text"}

    # Prepare the request data
    request_data = {
        #"model": "nousresearch/hermes-3-llama-3.1-405b:extended",  # Replace with your chosen model
        "model": "meta-llama/llama-3.1-405b-instruct",
        "messages": messages,
        "response_format": response_format,
    }

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    YOUR_SITE_URL = "loganzoellner.com"  # Optional, for rankings
    YOUR_APP_NAME = "loganzoellner.com"  # Optional, for rankings

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": f"{YOUR_SITE_URL}",  # Optional, for including your app on openrouter.ai rankings.
            "X-Title": f"{YOUR_APP_NAME}",  # Optional. Shows in rankings on openrouter.ai.
        },
        data=json.dumps(request_data),
    )

    # Process the response
    response_data = response.json()

    print(response_data)

    output_text = response_data["choices"][0]["message"]["content"]

    new_history = messages + [
        {"role": "assistant", "content": output_text},
    ]

    return output_text, new_history


