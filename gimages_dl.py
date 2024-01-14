import requests
from bs4 import BeautifulSoup
import urllib.request 
import csv
import os
import random
import glob


# Folder to save images 
save_folder = 'scraped_images'


def download_gimages(query: str, ):
    # Specify search term 
    search_term = query

    # Encode the search term to URL-friendly format
    encoded_term = urllib.parse.quote_plus(search_term) 

    # Construct Google Images query URL
    search_url = f"https://www.google.com/search?q={encoded_term}&tbm=isch"

    # Request Google Images page
    response = requests.get(search_url)


    # Create BeautifulSoup object from response
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all img tags 
    image_tags = soup.find_all('img')

    results =[]

    # Iterate over image tags
    for image in image_tags:

        # Get image source URL
        src = image.get('src')

        # Get image alt text 
        alt = image.get('alt') 

        # Store data
        image_data = {'src': src, 'alt': alt}

        # Add to results list 
        results.append(image_data)


    # Check if the directory already exists
    if not os.path.exists(save_folder):
        os.mkdir(save_folder)


    i = 0

    for image in results:
        url = image['src']
        title = i
        i += 1

    # Check if URL is a full URL
        if url.startswith('http') or url.startswith('https'):
            # Concatenate folder and file name
            file_name = f"{save_folder}/{title}.jpg"

            # Download image to folder
            urllib.request.urlretrieve(url, file_name)

#download_gimages('жираф')


def get_random_gimage():
    import random
    import os

    # Get a random image from the folder
    images = glob.glob(f"{save_folder}/*.jpg")
    random_image = random.choice(images)

    return random_image

#image_selected = get_random_gimage()

#print(image_selected)

#from short_model import get_categories_rn, get_categories_vit
#get_categories_rn(image_selected)