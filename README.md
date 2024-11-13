This is a program to generate a structured story.

It has wrappers for various llms:
* llama-cpp (local)
* xai
* chatgpt
* together
* gemini
* anthropic

And various image generators:
* comfyui (local)
* fal
* together

Currently you can disable/enable the correct generator by commenting/uncommenting the corresponding imports in
flaskApp1.py

Recommended configuration:
* gpt-4o-mini for chatJ (this handles tasks like converting between text and json)
* gemini/anthropic for chat (this does the creative writing)
* comfyui/fal for image generation (FAL is expensive, but doesn't require a powerful GPU)

If using comfyui for image generation, make sure that you use the --use_comfy and the --comfy_yaml <your_yaml_file.yaml> arguments.

comfy.py is a wrapper around the comfyui API.  

Note that if you want to use a custom model, you can export as API and write a corresponding comfy.yaml file for it.

Note that for remote models (OpenAI, FAL, etc.) you will need to set your API keys as environment variables.

Once you have everything you should be able to run

python flaskApp1.py 

This should open a webserver on localhost:5000.

On this page, there should be a text box where you can input a plot and a "play" button.

Clicking the play button should generate a story based on your plot and play it.

Note that the story will take a bit to get started as it needs to generate things like a plot outline.

I recommend watching the command line to make sure that no errors are showing up.