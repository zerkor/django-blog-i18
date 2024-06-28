import openai
from decouple import config

print("Loading API key...")
# Chargez votre clé API OpenAI depuis le fichier .env
openai.api_key = config('OPENAI_API_KEY')
print("API key loaded.")

try:
    # Envoyez une requête de test à l'API OpenAI
    print("Sending request to OpenAI...")
    response = openai.Completion.create(
        engine="gpt-3.5-turbo",
        prompt="Say this is a test",
        max_tokens=5
    )
    print("Response from OpenAI:", response.choices[0].text.strip())
except Exception as e:
    print("Error:", e)
