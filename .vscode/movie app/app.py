import customtkinter as ctk
from ui import MovieAppUI

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Movie Explorer")
app.geometry("500x700")

MovieAppUI(app)

app.mainloop()
