import requests
from config import TMDB_API_KEY, BASE_URL


def search_movie(query):
    url = f"{BASE_URL}/search/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "query": query
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("results", [])


def get_popular_movies():
    url = f"{BASE_URL}/movie/popular"
    params = {"api_key": TMDB_API_KEY}

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("results", [])
