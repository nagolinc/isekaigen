from google.generativeai.types import HarmCategory, HarmBlockThreshold

import os

import google.generativeai as genai



def chat(
    input_text,
    system_prompt="do your best",
    history=None,
    json_mode=False,
    #model="gemini-1.5-flash",
    model="gemini-1.5-pro",
    max_history=8,
):

    if history is None:
        #    history = [{"role": "system", "content": system_prompt}]
        history = []

    if json_mode:
        response_format = "application/json"
    else:
        response_format = "text/plain"

    # Create the model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 16384,
        "response_mime_type": response_format,
    }

    model = genai.GenerativeModel(
        model_name=model,
        generation_config=generation_config,
        # safety_settings = Adjust safety settings
        # See https://ai.google.dev/gemini-api/docs/safety-settings
        system_instruction=system_prompt,
        safety_settings={
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory. HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory. HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.  HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
    }

    )

    if len(history) > max_history:
        history = history[-max_history:]

    messages = history

    chat_session = model.start_chat(
        history=messages,
    )

    response = chat_session.send_message(input_text)

    output_text = response.text

    new_history = messages + [
        {"role": "user", "parts": [input_text]},
        {"role": "model", "parts": [output_text]},
    ]

    return output_text, new_history