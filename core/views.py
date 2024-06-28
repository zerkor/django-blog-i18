from django.shortcuts import render
from .models import Post
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
import openai
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import logging

# Configurez votre clé API OpenAI
openai.api_key = settings.OPENAI_API_KEY

# Configurer le logging
logger = logging.getLogger(__name__)

# Indexation des articles de blog
def index_blog_posts():
    posts = Post.objects.all()
    documents = [post.content for post in posts]
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(documents).toarray()

    # Créer l'index FAISS
    dimension = vectors.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(vectors, dtype=np.float32))
    return vectorizer, index, posts

vectorizer, index, posts = index_blog_posts()

def index(request):
    if request.user.is_authenticated:
        messages.success(request, _("authmessage {first} {last}").format(first=request.user.first_name, last=request.user.last_name), extra_tags="alert alert-success")
    else:
        messages.warning(request, _("anonmessage"), extra_tags="alert alert-danger")

    posts = Post.objects.all()

    context = {'posts': posts}
    return render(request, 'index.html', context)

@csrf_exempt
def chatbot(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')

            if not user_message:
                logger.warning("No message provided in the request.")
                return JsonResponse({"error": "No message provided"}, status=400)

            logger.info("User message: %s", user_message)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=150
            )

            logger.info("OpenAI response: %s", response)
            response_text = response.choices[0].message['content'].strip()
            print(f"OpenAI response: {response_text}")
            return JsonResponse({"response": response_text})
        except openai.error.OpenAIError as e:
            logger.error("OpenAI error: %s", e)
            print(f"OpenAI error: {e}")
            return JsonResponse({"error": str(e)}, status=500)
        except Exception as e:
            logger.error("Error processing request: %s", e)
            print(f"Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    return render(request, "chatbot.html")

@csrf_exempt
def search(request):
    query = request.GET.get('query')
    if not query:
        logger.warning("No query provided in the search request.")
        return JsonResponse({"error": "No query provided"}, status=400)

    query_vector = vectorizer.transform([query]).toarray().astype(np.float32)
    _, indices = index.search(query_vector, k=5)
    results = [posts[i] for i in indices[0]]
    logger.info("Search results: %s", results)

    # Augmenter les résultats avec l'API OpenAI
    augmented_results = []
    for post in results:
        response = openai.Completion.create(
            model="gpt-3.5-turbo",
            prompt=f"Summarize the following content: {post.content}",
            max_tokens=50
        )
        summary = response.choices[0].text.strip()
        augmented_results.append({
            "title": post.title,
            "summary": summary,
            "url": post.get_absolute_url()
        })

    return JsonResponse({"results": augmented_results})
