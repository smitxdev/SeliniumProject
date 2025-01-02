# Import the required libraries
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from google.cloud import translate_v2 as translate
import os
import requests
import re

# Automatically download and use the correct ChromeDriver
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# Directory to save images
image_dir = "article_images"
os.makedirs(image_dir, exist_ok=True)

# Set the path to your Google Cloud credentials JSON file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "decisive-coda-446415-j1-c4edbcf8e92c.json"

# Initialize Google Cloud Translate client
translate_client = translate.Client()

# Translate function using Google Cloud Translate API
def translate_text(text, target_language='en'):
    result = translate_client.translate(text, target_language=target_language)  # Corrected argument name
    return result['translatedText']

# Try case handling
try:
    # Debugger
    print("Opening the Editoriales section...")
    
    # Get the articles from the link
    driver.get("https://elpais.com/opinion/editoriales/")
    
    # Wait until the page loads completely
    print("Waiting for the Editoriales page to load...")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    print("Editoriales page loaded.")

    # Handle the cookies popup using the provided XPath
    try:
        # Debugger
        print("Looking for the cookies popup...")
        
        # Accept the cookies
        cookies_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="didomi-notice-agree-button"]'))
        )
        cookies_button.click()
        
        # Debugger
        print("Cookies popup accepted.")
    
    except Exception as e:
        print("Cookies popup not found or already handled:", e)

    # Initialize a dictionary to store articles
    articles_dict = {}
    article_links = []

    # Locate all article elements inside the main div
    print("Fetching links for the top 5 articles...")
    main_div = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '/html/body/main/div/div[2]'))
    )

    # Get the top 5 articles
    articles = main_div.find_elements(By.TAG_NAME, "article")[:5]  # Get top 5 articles

    # Collect links for the top 5 articles
    for index, article in enumerate(articles, 1):
        # Get the titles
        title_element = article.find_element(By.XPATH, './header/h2/a')
        
        # Extract the text of the title
        title = title_element.text

        # Extract the link
        link = title_element.get_attribute("href")
        
        # Append to the articles list
        article_links.append((title, link))
        
        # Debugger
        print(f"Article {index} Title: {title} | Link: {link}")

    # Navigate to each article using the stored links
    for index, (title, link) in enumerate(article_links, 1):
        # Debugger
        print(f"\nProcessing Article {index}: {title} ({link})")

        # Navigate to the article page
        driver.get(link)

        # Wait for the specific content to load inside the article
        print(f"Fetching content for Article {index}...")
        article_content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/article/div[2]'))
        )
        content_text = article_content.text

        # Store the title and content in the dictionary
        articles_dict[title] = content_text
        print(f"Content for Article {index} fetched.")

        # Fetch the image from the article
        try:
            print(f"Fetching image for Article {index}...")
            image_element = driver.find_element(By.XPATH, '/html/body/article/header/div[2]/figure/span/img')
            image_url = image_element.get_attribute("src")

            # Download the image
            response = requests.get(image_url)
            if response.status_code == 200:
                image_path = os.path.join(image_dir, f"article_{index}.jpg")
                with open(image_path, "wb") as img_file:
                    img_file.write(response.content)
                print(f"Image for Article {index} saved at {image_path}.")
            else:
                print(f"Failed to download image for Article {index}.")
        except Exception as e:
            print(f"Image not found for Article {index}: {e}")

    # Print the results
    print("\nArticles fetched: ")
    for title, content in articles_dict.items():
        print(f"\nTitle: {title}\nContent: {content}\n")

    # Translate the titles to English using Google Translate API
    print("\nTranslating article titles to English...")
    
    # Define the list for translated_titles
    translated_titles = []
    
    # Iterate on the article links
    for index, (title, link) in enumerate(article_links, 1):
        translated_title = translate_text(title, target_language='en')  # Using Google Cloud Translate API
        translated_titles.append((translated_title, link))

        print("=====================================Title English Translation=============================================================")
        print(f"Article {index} Original Title: {title}")
        print(f"Article {index} Translated Title: {translated_title}")
        print("")

    # Analyze the translated headers for repeated words
    print("\nAnalyzing repeated words in translated titles...")
    all_words = []
    for translated_title, link in translated_titles:  # Extract only the title
        # Clean and split words
        words = re.findall(r'\w+', translated_title.lower())  # Convert to lowercase and extract words
        all_words.extend(words)

    # Count the occurrences of each word
    from collections import Counter
    word_counts = Counter(all_words)

    # Identify words repeated more than twice
    repeated_words = {word: count for word, count in word_counts.items() if count > 2}
    if repeated_words:
        print("\nRepeated words (occurring more than twice):")
        for word, count in repeated_words.items():
            print(f"{word}: {count}")
    else:
        print("No words are repeated more than twice.")

# Close all the resources
finally:
    # Debugger
    print("Closing the browser...")
    driver.quit()
