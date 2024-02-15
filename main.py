import io
import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
from datetime import datetime

def set_style():
    style = ttk.Style()
    style.theme_use('alt')

    # Colors
    bgColor = "#790909"  # Dark red background
    inputBg = "#ffffff"  # White Background for inputs
    inputFg = '#000000'
    btnBg = "#ec0d0d"  # Button background
    btnFg = "#ffffff"  # Button text color
    txtFg = "#ffffff"  # Text color

    # Button style
    style.configure('TButton', background=btnBg, foreground=btnFg, font=('Arial', 10, 'bold'), borderwidth=1)
    style.map('TButton', background=[('active', btnBg)], foreground=[('active', btnFg)], font='helvetica 24')

    # Label style
    style.configure('TLabel', background=bgColor, foreground=txtFg, font=('Arial bold', 14))

    # Entry style
    style.configure('TEntry', background=inputBg, foreground=inputFg, fieldbackground=inputBg, borderwidth=1)

def fetch_pokemon_data(pokemon):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon.lower()}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        messagebox.showerror("Error", "Could not find Pokémon")
        return None

def open_registration_page():
    registration_window = tk.Tk()
    registration_window.title("Registration")
    registration_window.resizable(0,0)
    registration_window.geometry("400x350")
    registration_window.configure(bg="#790909")

    set_style()  # Apply style to the register page

    registration_frame = ttk.Frame(registration_window)
    registration_frame.place(relx=0.5, rely=0.5, anchor='center')

    ttk.Label(registration_frame, text="Username:").grid(row=0, column=0, padx=10, pady=10)
    username_entry_reg = ttk.Entry(registration_frame)
    username_entry_reg.grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(registration_frame, text="Password:").grid(row=1, column=0, padx=10, pady=10)
    password_entry_reg = ttk.Entry(registration_frame, show="*")
    password_entry_reg.grid(row=1, column=1, padx=10, pady=10)

    def register_user():
        username_reg = username_entry_reg.get()
        password_reg = password_entry_reg.get()

        if not username_reg or not password_reg:
            messagebox.showerror("Registration Error", "Please fill in all fields.")
            return

        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username_reg,))
        
        if cursor.fetchone():
            messagebox.showerror("Registration Error", "Username already exists.")
        else:
            registration_date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('INSERT INTO users (username, password, registration_date) VALUES (?, ?, ?)', (username_reg, password_reg, registration_date))
            conn.commit()
            conn.close()
            messagebox.showinfo("Registration Info", "Registration successful. You can now login.")
            registration_window.destroy()

    register_button = ttk.Button(registration_frame, text="Register", command=register_user)
    register_button.grid(row=2, column=0, columnspan=2, pady=10)

    registration_window.mainloop()

def fetch_user_data():
    global logged_in_user
    if logged_in_user:
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username, registration_date FROM users WHERE username = ?', (logged_in_user,))
        user_data = cursor.fetchone()
        conn.close()
        return user_data
    return None

def get_account_age(registration_date):
    registration_date = datetime.strptime(registration_date, '%Y-%m-%d')
    current_date = datetime.now()
    age = current_date - registration_date
    return age.days


def display_pokemon_data():
    pokemon_name_or_id = search_entry.get()
    data = fetch_pokemon_data(pokemon_name_or_id)

    if data:
        pokemon_name.config(text=data['name'].title())
        pokemon_type.config(text=', '.join([t['type']['name'].title() for t in data['types']]))

        # Fetch and display the pokemon
        sprite_url = data['sprites']['front_default']
        response = requests.get(sprite_url)
        image_bytes = io.BytesIO(response.content)
        pil_image = Image.open(image_bytes)
        tk_image = ImageTk.PhotoImage(pil_image)

        pokemon_sprite.config(image=tk_image)
        pokemon_sprite.image = tk_image

global logged_in_user
logged_in_user = ""

def setup_database():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            registration_date DATE NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def raise_frame(frame):
    frame.tkraise()

def open_user_dashboard():
    dashboard = tk.Tk()
    dashboard.title("User Dashboard")
    dashboard.resizable(0,0)
    dashboard.geometry("450x350")
    dashboard.configure(bg="#790909")

    set_style()  # Apply the style

    # Create different menus
    home_frame = ttk.Frame(dashboard)
    party_frame = ttk.Frame(dashboard)
    search_frame = ttk.Frame(dashboard)

    for frame in (home_frame, party_frame, search_frame):
        frame.grid(row=0, column=0, sticky='nsew')
        dashboard.grid_columnconfigure(0, weight=1)
        dashboard.grid_rowconfigure(0, weight=1)

    user_data = fetch_user_data()

    if user_data:
        username_label = ttk.Label(home_frame, text=f"WELCOME, {user_data[0]}!")
        username_label.place(x=140,y=20)

        account_age = get_account_age(user_data[1])
        age_label = ttk.Label(home_frame, text=f"Account Age: {account_age} days")
        age_label.place(x=70, y=200)

    ttk.Label(party_frame, text="Welcome to the Party Menu!").pack(pady=20)
    
    global search_entry, pokemon_name, pokemon_type, pokemon_sprite

    search_entry = ttk.Entry(search_frame)
    search_entry.pack(pady=10)

    search_button = ttk.Button(search_frame, text="Search", command=display_pokemon_data)
    search_button.pack(pady=5)

    pokemon_name = ttk.Label(search_frame, text="")
    pokemon_name.pack(pady=5)

    pokemon_type = ttk.Label(search_frame, text="")
    pokemon_type.pack(pady=5)

    pokemon_sprite = ttk.Label(search_frame)
    pokemon_sprite.pack(pady=5)

    menu_bar = tk.Menu(dashboard)
    dashboard.config(menu=menu_bar)

    menu_bar.add_command(label="Home", command=lambda: raise_frame(home_frame))
    menu_bar.add_command(label="Party", command=lambda: raise_frame(party_frame))
    menu_bar.add_command(label="Search", command=lambda: raise_frame(search_frame))

    raise_frame(home_frame)

    dashboard.mainloop()

def login():
    global logged_in_user
    username = username_entry.get()
    password = password_entry.get()

    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    
    if cursor.fetchone():
        logged_in_user = username  # Set the logged-in user
        messagebox.showinfo("Login Info", "Successfully Logged In")
        root.destroy()  # Close the login window
        open_user_dashboard()  # Open the user dashboard
    else:
        messagebox.showerror("Login Info", "Invalid Credentials")
    
    conn.close()

# Create the main window
def main_login_window():
    global root, username_entry, password_entry
    root = tk.Tk()
    root.resizable(0,0)
    root.title("Pokedex")
    root.geometry("450x350")
    root.configure(bg="#790909")

    set_style()  # Apply style to the login window

    # Centering the Login Page
    login_frame = ttk.Frame(root)
    login_frame.place(relx=0.5, rely=0.5, anchor='center')

    ttk.Label(login_frame, text="Username:").grid(row=0, column=0, padx=10, pady=10)
    username_entry = ttk.Entry(login_frame)
    username_entry.grid(row=0, column=1, padx=10, pady=10)

    ttk.Label(login_frame, text="Password:").grid(row=1, column=0, padx=10, pady=10)
    password_entry = ttk.Entry(login_frame, show="*")
    password_entry.grid(row=1, column=1, padx=10, pady=10)

    register_button = ttk.Button(login_frame, text="Register", command=open_registration_page)
    register_button.grid(row=3, column=0, columnspan=2, pady=10)

    login_button = ttk.Button(login_frame, text="Login", command=login)
    login_button.grid(row=2, column=0, columnspan=2, pady=10)

    setup_database()

    root.mainloop()

if __name__ == "__main__":
    main_login_window()
