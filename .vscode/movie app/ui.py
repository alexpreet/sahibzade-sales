import customtkinter as ctk
from api import search_movie
from PIL import Image
import requests
from io import BytesIO
from config import IMAGE_BASE_URL


class MovieAppUI(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True, padx=20, pady=20)

        self.title = ctk.CTkLabel(self, text="🎬 Movie Explorer", font=("Arial", 24))
        self.title.pack(pady=10)

        self.search_entry = ctk.CTkEntry(self, placeholder_text="Search for a movie...")
        self.search_entry.pack(fill="x", pady=10)

        self.search_button = ctk.CTkButton(
            self, text="Search", command=self.search_movies
        )
        self.search_button.pack(pady=5)

        self.result_label = ctk.CTkLabel(self, text="")
        self.result_label.pack(pady=10)

        self.poster_label = ctk.CTkLabel(self, text="")
        self.poster_label.pack(pady=10)

    def search_movies(self):
        query = self.search_entry.get().strip()
        if not query:
            self.result_label.configure(text="Please enter a movie name.")
            return

        movies = search_movie(query)

        if not movies:
            self.result_label.configure(text="No results found.")
            self.poster_label.configure(image=None)
            return

        movie = movies[0]
        title = movie.get("title", "N/A")
        rating = movie.get("vote_average", "N/A")
        release = movie.get("release_date", "N/A")

        self.result_label.configure(
            text=f"{title}\n⭐ Rating: {rating}\n📅 Release: {release}"
        )

        poster_path = movie.get("poster_path")
        if poster_path:
            img_url = IMAGE_BASE_URL + poster_path
            img_data = requests.get(img_url).content
            image = Image.open(BytesIO(img_data)).resize((200, 300))
            poster = ctk.CTkImage(image, size=(200, 300))
            self.poster_label.configure(image=poster)
            self.poster_label.image = poster
