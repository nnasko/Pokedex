import io
import os
import tkinter as tk
from tkinter import ttk
import sqlite3
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
from datetime import datetime

newuser = -1
image_references = {}

image_cache_dir = 'pokemon_images'
if not os.path.exists(image_cache_dir):
    os.makedirs(image_cache_dir)

def set_style():
    style = ttk.Style()
    style.theme_use('alt')

    # Colors
    bgColor = "#790909"  # Dark red background
    inputBg = "#ffffff"  # White Background for inputs
    inputFg = '#000000' # White Foreground  
    btnBg = "#6A1010"  # Button background
    btnFg = "#ffffff"  # Button text color
    txtFg = "#ffffff"  # Text color

    # Button style
    style.configure('TButton', background=btnBg, foreground=btnFg, font=('Arial', 10, 'bold'), borderwidth=1)
    style.map('TButton', background=[('active', btnBg)], foreground=[('active', btnFg)], font='helvetica 14')

    style.configure('Switch.TButton', background='#6A1010', foreground='#ffffff', font=('Arial', 10, 'bold'), borderwidth=1)
    style.map('Switch.TButton', background=[('active', '#6A1010'), ('pressed', '#5e0f0f')], foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])

    # Label style
    style.configure('TLabel', background=bgColor, foreground=txtFg, font=('Arial bold', 14))

    # Entry style
    style.configure('TEntry', background=inputBg, foreground=inputFg, fieldbackground=inputBg, borderwidth=1)

def fetch_pokemon_data(pokemon):
    pokemon = str(pokemon)
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
            default_pokemon_ids = [1, 4, 7, 32, 11, 282]
            for pokemon_id in default_pokemon_ids:
                cursor.execute('INSERT INTO user_pokemon (username, pokemon_id) VALUES (?, ?)', (username_reg, pokemon_id))
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

def fetch_pokemon_image(pokemon_id):
    local_image_path = os.path.join(image_cache_dir, f'{pokemon_id}.png')
    # Check if the image is already downloaded
    if os.path.isfile(local_image_path):
        return Image.open(local_image_path)
    
    # If not fetch it from the API
    data = fetch_pokemon_data(pokemon_id)
    if data and 'sprites' in data and 'front_default' in data['sprites']:
        sprite_url = data['sprites']['front_default']
        response = requests.get(sprite_url)
        if response.status_code == 200:
            with open(local_image_path, 'wb') as image_file:
                image_file.write(response.content)
            return Image.open(local_image_path)
    return None  # Return None if there is no image

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

def fetch_user_pokemon(username):
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT pokemon_id FROM user_pokemon WHERE username = ?', (username,))
    pokemon_ids = cursor.fetchall()
    conn.close()
    return [id[0] for id in pokemon_ids]

def display_user_pokemon(frame, pokemon_ids):
    image_size = (80, 80)  # Width, height in pixels
    global image_references  # Use the global image_references dictionary
    
    # Clear previous widgets in the frame but not the image references
    for widget in frame.winfo_children():
        widget.destroy()
    
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(1, weight=1)
    frame.grid_columnconfigure(2, weight=1)

    # Configure additional row weights as needed
    for i in range((len(pokemon_ids) + 2) // 3):
        frame.grid_rowconfigure(i, weight=1)
    
    for i, pokemon_id in enumerate(pokemon_ids):
        pil_image = fetch_pokemon_image(pokemon_id)
        if pil_image:
            pil_image = pil_image.resize(image_size)
            tk_image = ImageTk.PhotoImage(pil_image)
            
            image_references[pokemon_id] = tk_image

            label = ttk.Label(frame, image=tk_image, background='white')
            label.image = tk_image
            label.grid(row=2 * (i // 3), column=i % 3, padx=10, pady=10)

            switch_button_command = lambda pid=pokemon_id: create_switch_window(pid, update_user_pokemon)
            button = ttk.Button(frame, text="SWITCH", style='Switch.TButton', command=switch_button_command)
            button.grid(row=2 * (i // 3) + 1, column=i % 3, padx=10, pady=10)
        else:
            messagebox.showinfo("Image Error", f"No image available for Pokémon ID: {pokemon_id}")


def setup_database():
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            registration_date DATE NOT NULL,
            PRIMARY KEY(username)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_pokemon (
            username TEXT NOT NULL,
            pokemon_id INTEGER NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username)
        )
    ''')
    conn.commit()
    conn.close()


def change_username():
    global changeuser_entry
    newuser = changeuser_entry.get()
    print(newuser)
    olduser = logged_in_user
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    exec = f"UPDATE users SET username='{newuser}' WHERE username='{olduser}'"
    print(exec)
    cursor.execute(exec)
    conn.commit()
    conn.close()
    exit()


def raise_frame(frame):
    frame.tkraise()

def open_user_dashboard():
    dashboard = tk.Tk()
    global changeuser_entry, image_references
    dashboard.title("User Dashboard")
    dashboard.resizable(0,0)
    icon = ImageTk.PhotoImage(file="pokeball.ico")
    dashboard.iconphoto(False, icon)
    dashboard.geometry("450x350")

    set_style()  # Apply the style

    # Create different menus
    home_frame = tk.Frame(dashboard, bg='#790909')
    party_frame = tk.Frame(dashboard, bg='#790909')
    search_frame = tk.Frame(dashboard, bg='#790909')

    for frame in (home_frame, party_frame, search_frame):
        frame.grid(row=0, column=0, sticky='nsew')
    dashboard.grid_columnconfigure(0, weight=1)
    dashboard.grid_rowconfigure(0, weight=1)

    user_data = fetch_user_data()
    user_pokemon_ids = fetch_user_pokemon(logged_in_user)
    display_user_pokemon(party_frame, user_pokemon_ids)

    if user_data:
        img = ImageTk.PhotoImage(Image.open('ash.png'))
        panel = tk.Label(home_frame, image = img, highlightbackground="black", highlightthickness=2)
        panel.place(x=20, y=20)

        username_label = ttk.Label(home_frame, text=f"WELCOME, {user_data[0]}!", font="helvetica 16 bold")
        username_label.place(x=220,y=20)

        changeuser_label = ttk.Label(home_frame, text="Change Username:", font="helvetica 10 normal")
        changeuser_label.place(x=220 ,y=60)

        changeuser_entry = ttk.Entry(home_frame)
        changeuser_entry.place(x=220 ,y=85)

        changeuser_button = tk.Button(home_frame, text="CHANGE", height=1, width=10, background="#6A1010", foreground="#ffffff", command=change_username)
        changeuser_button.place(x=360, y=85)

        account_age = get_account_age(user_data[1])
        age_label = ttk.Label(home_frame, text=f"Account Age: {account_age} days", font="helvetica 12 roman")
        age_label.place(x=15, y=170)

        delete_button = ttk.Button(home_frame, text="DELETE ACCOUNT", command=delete_account, padding=8)
        delete_button.place(x=10, y=200)
    
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
    menu_bar.add_command(label="Party", command=lambda: [raise_frame(party_frame), display_user_pokemon(party_frame, user_pokemon_ids)])
    menu_bar.add_command(label="Search", command=lambda: raise_frame(search_frame))

    raise_frame(home_frame)

    dashboard.mainloop()

def create_switch_window(old_pokemon_id, update_callback):
    switch_window = tk.Toplevel()
    switch_window.title("Switch Pokémon")
    switch_window.geometry("257x112")  # Set the window size to match the provided design
    switch_window.configure(bg='#790909')  # Set the same background color

    # Label for the entry field
    entry_label = tk.Label(switch_window, text="Enter Pokémon Name/ID:", bg='#790909', fg='white')
    entry_label.pack(pady=(10, 0))
    new_pokemon_id = tk.StringVar(switch_window)

    def search_pokemon():
        pokemon_name_or_id = pokemon_entry.get()
        data = fetch_pokemon_data(pokemon_name_or_id)
        if data:
            new_pokemon_id.set(str(data['id']))  # Store the new Pokémon ID
            pil_image = fetch_pokemon_image(data['id'])
            if pil_image:
                pil_image = pil_image.resize((80, 80))  # Resize the image to fit the label
                tk_image = ImageTk.PhotoImage(pil_image)
                pokemon_image_label.configure(image=tk_image)
                pokemon_image_label.image = tk_image  # Keep a reference
            else:
                messagebox.showerror("Error", "Could not find Pokémon")
        else:
            messagebox.showerror("Error", "Could not find Pokémon")

    def confirm_switch():
        # Use the nonlocal keyword to modify the new_pokemon_id outside of the nested function
        nonlocal new_pokemon_id
        if new_pokemon_id:
            update_callback(old_pokemon_id, new_pokemon_id)  # Use the old_pokemon_id from the function argument
            switch_window.destroy()

    # Entry widget where the user will type the new Pokémon name/ID
    pokemon_entry = tk.Entry(switch_window, width=20)
    pokemon_entry.pack(pady=5)

    # Search button to find the new Pokémon
    search_button = tk.Button(switch_window, text="Search", bg='#6A1010', fg='white', command=search_pokemon)
    search_button.pack(side=tk.LEFT, padx=(20, 10))

    # Confirm button to confirm the switch
    confirm_button = tk.Button(switch_window, text="CONFIRM", bg='#6A1010', fg='white', command=confirm_switch)
    confirm_button.pack(side=tk.RIGHT, padx=(10, 20))

    # Pokemon image (use a placeholder or fetch dynamically)
    pokemon_image_label = tk.Label(switch_window, bg='white')
    pokemon_image_label.pack(pady=5)
    # You would set the image for the label here using the Pokémon ID if available
    # For now, let's use a placeholder
    placeholder_image_path = 'path_to_placeholder_pokemon_image.png'
    pil_image = Image.open(placeholder_image_path)
    tk_image = ImageTk.PhotoImage(pil_image)
    pokemon_image_label.configure(image=tk_image)
    pokemon_image_label.image = tk_image  # Keep a reference

    switch_window.mainloop()

def update_user_pokemon(old_pokemon_id, new_pokemon_id):
    # Update the user_pokemon in the database
    new_pokemon_id = new_pokemon_id.get()

    try:
        new_pokemon_id = int(new_pokemon_id)
    except ValueError:
        messagebox.showerror("Error", "Invalid Pokémon ID")
        return

    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE user_pokemon SET pokemon_id = ? WHERE username = ? AND pokemon_id = ?', (new_pokemon_id, logged_in_user, old_pokemon_id))
    conn.commit()
    conn.close()

    # Update the image_references to show the new Pokemon image
    pil_image = fetch_pokemon_image(new_pokemon_id)
    if pil_image:
        pil_image = pil_image.resize((80, 80))
        tk_image = ImageTk.PhotoImage(pil_image)
        # Update the image for the old Pokemon ID with the new image
        image_label = image_references[old_pokemon_id]
        image_label.configure(image=tk_image)
        image_label.image = tk_image  # Keep a reference
        # Update the image_references dictionary with the new Pokemon ID
        image_references[new_pokemon_id] = image_references.pop(old_pokemon_id)

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

def delete_account():
    username = logged_in_user
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    delete = f"DELETE FROM users WHERE username LIKE '{username}'"
    cursor.execute(delete)
    conn.commit()
    conn.close()
    exit() 


# Create the main window
def main_login_window():
    global root, username_entry, password_entry
    root = tk.Tk()
    root.resizable(0,0)
    root.title("Pokedex")
    root.geometry("450x350")
    icon = ImageTk.PhotoImage(file = "pokeball.ico")
    root.iconphoto(False, icon)
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
    setup_database()