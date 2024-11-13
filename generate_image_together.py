import os
from together import Together
import datetime
import re
import json
import base64

from PIL import Image
from io import BytesIO
    


def generate_image(prompt,save_dir="static/samples"):

    client = Together(api_key=os.environ.get('TOGETHER_API_KEY'))
    response = client.images.generate(
        prompt=prompt,
        model="black-forest-labs/FLUX.1-schnell-Free",
        #width=1024,
        #height=768,
        #width=1440,
        #height=832,
        width=1024,
        height=576,
        steps=4,
        n=1,
        response_format="b64_json"
    )
    #print(response.data[0].b64_json[:100])
    
    
    
    #deode base64 and json
    d=base64.b64decode(response.data[0].b64_json)
    
    #d contains the data of a jpeg image, let's convert it to PIL
    pilImage=Image.open(BytesIO(d))
    
    
    #filename should look like {datetime}-{prompt with nonletters repacedw ith _}
    sanitized_prompt = re.sub('[^a-zA-Z0-9]', '_', prompt)[:50]
    sanitized_datetime = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename = f"{sanitized_datetime}_{sanitized_prompt}.jpg"
    
    #save the image
    pilImage.save(f"{save_dir}/{filename}")
        
    return f"{save_dir}/{filename}"
        
if __name__=="__main__":        
    filename=generate_image("a cat in a hat")        
    print(f"Image saved to {filename}")
    