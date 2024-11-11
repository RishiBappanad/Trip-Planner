import requests
import tkinter as tk
from tkinter import *
import itenerary as itenerary
from place import Place
import urllib.parse

FOURSQUARE_API_KEY = 
client_secret = 
client_id = 


class ScrollableFrame(Frame):
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        canvas = Canvas(self)
        scrollbar = Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class TripPlannerUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Trip Planner")
        self.geometry("400x1000")

        # Scrollable Frame
        container = ScrollableFrame(self)
        container.pack(fill="both", expand=True)

        self.itinerary = itenerary.Itinerary()

        tk.Label(container.scrollable_frame, text="Enter Location:").pack(pady=5)
        self.location_entry = tk.Entry(container.scrollable_frame)
        self.location_entry.pack(pady=5)

        # Add a Listbox for suggestions
        self.suggestions_listbox = tk.Listbox(self, height=5)
        self.suggestions_listbox.place_forget()
        self.suggestions_listbox.bind("<ButtonRelease-1>", self.select_suggestion)

        # Bind location entry change event to update suggestions
        self.location_entry.bind("<KeyRelease>", self.on_location_entry_change)

        tk.Label(container.scrollable_frame, text="Transportation:").pack(pady=5)
        self.car_var = tk.BooleanVar()
        self.car_check = tk.Checkbutton(container.scrollable_frame, text="Rent a Car", variable=self.car_var)
        self.car_check.pack(pady=5)

        tk.Label(container.scrollable_frame, text="Hotel Budget per Night:").pack(pady=5)
        self.budget_slider = tk.Scale(container.scrollable_frame, from_=50, to_=1000, orient=tk.HORIZONTAL)
        self.budget_slider.pack(pady=5)

        tk.Label(container.scrollable_frame, text="Stay Duration (days):").pack(pady=5)
        self.duration_slider = tk.Scale(container.scrollable_frame, from_=1, to_=30, orient=tk.HORIZONTAL)
        self.duration_slider.pack(pady=5)

        tk.Label(container.scrollable_frame, text="Dining Preferences:").pack(pady=5)
        self.canvas = tk.Canvas(container.scrollable_frame, width=300, height=50)
        self.canvas.pack(pady=5)

        self.pos1 = 100
        self.pos2 = 200
        self.draw_slider()

        self.canvas.bind("<B1-Motion>", self.move_handle)
        self.canvas.bind("<Button-1>", self.move_handle)

        tk.Label(container.scrollable_frame, text="Tours:").pack(pady=5)
        self.tours_options = tk.Listbox(container.scrollable_frame, selectmode=tk.MULTIPLE)
        tours = ["City Tour", "Museum Tour", "Nature Tour", "Historical Tour", "Physical Activity"]
        for tour in tours:
            self.tours_options.insert(tk.END, tour)
        self.tours_options.pack(pady=5)

        self.submit_button = tk.Button(container.scrollable_frame, text="Submit", command=self.submit)
        self.submit_button.pack(pady=20)

    def on_location_entry_change(self, event):
        query = self.location_entry.get()
        if len(query) > 2:
            suggestions = self.get_autocomplete_suggestions(query)
            self.update_suggestions_list(suggestions)

    def get_autocomplete_suggestions(self, query):
        url = "https://api.foursquare.com/v3/autocomplete"
        headers = {
            "accept": "application/json",
            "Authorization": FOURSQUARE_API_KEY,
        }
        params = {
            "query": query,
            "limit": 10,
            "types": "geo"
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get('results', [])
        else:
            print(f"Error fetching suggestions: {response.status_code}")
            return []

    def update_suggestions_list(self, suggestions):
        self.suggestions_listbox.delete(0, tk.END)
        for suggestion in suggestions:
            display_text = suggestion['text']['primary']
            self.suggestions_listbox.insert(tk.END, display_text)

    def select_suggestion(self, event):
        selected_index = self.suggestions_listbox.curselection()
        if selected_index:
            selected_text = self.suggestions_listbox.get(selected_index)
            self.location_entry.delete(0, tk.END)
            self.location_entry.insert(0, selected_text)
            self.suggestions_listbox.delete(0, tk.END)

    def draw_slider(self):
        self.canvas.delete("all")

        self.canvas.create_line(50, 25, 250, 25, fill="gray", width=2)
        self.canvas.create_line(50, 25, self.pos1, 25, fill="red", width=6)
        self.canvas.create_line(self.pos1, 25, self.pos2, 25, fill="green", width=6)
        self.canvas.create_line(self.pos2, 25, 250, 25, fill="blue", width=6)
        self.canvas.create_oval(self.pos1 - 5, 20, self.pos1 + 5, 30, fill="black")
        self.canvas.create_oval(self.pos2 - 5, 20, self.pos2 + 5, 30, fill="black")

        fast_food_percent = int(((self.pos1 - 50) / 200) * 100)
        local_food_percent = int(((self.pos2 - self.pos1) / 200) * 100)
        upscale_dining_percent = 100 - fast_food_percent - local_food_percent

        self.canvas.create_text(25, 25, text=f"{fast_food_percent}%")
        self.canvas.create_text(150, 25, text=f"{local_food_percent}%")
        self.canvas.create_text(275, 25, text=f"{upscale_dining_percent}%")

    def move_handle(self, event):
        if 50 <= event.x <= 250:
            if abs(event.x - self.pos1) < abs(event.x - self.pos2):
                self.pos1 = max(50, min(event.x, self.pos2 - 10))
            else:
                self.pos2 = min(250, max(event.x, self.pos1 + 10))
            self.draw_slider()

    def submit(self):
        location = self.location_entry.get()
        rent_car = self.car_var.get()
        self.itinerary.mode = "driving" if rent_car else "transit"
        budget = self.budget_slider.get()
        duration = self.duration_slider.get()

        fast_food_percent = int(((self.pos1 - 50) / 200) * 100)
        local_food_percent = int(((self.pos2 - self.pos1) / 200) * 100)
        upscale_dining_percent = 100 - fast_food_percent - local_food_percent

        selected_tours = [self.tours_options.get(i) for i in self.tours_options.curselection()]

        print(f"Location (City, State/Province, Country): {location}")
        print(f"Rent a Car: {rent_car}")
        print(f"Hotel Budget per Night: ${budget}")
        print(f"Stay Duration: {duration} days")
        print(
            f"Dining Preferences: Fast Food {fast_food_percent}%, Local Food {local_food_percent}%, Upscale Dining {upscale_dining_percent}%")
        print(f"Selected Tours: {selected_tours}")

        '''
                try:
                    return_places = []
                    for tour_type in selected_tours:
                        places = self.search_places(location, query=tour_type)
                        for i in range(2):
                            return_places.append(places[i])
                    for place in return_places:
                        try:
                            print(f"{place['name']} at {place['location']['address']}")
                        except KeyError:
                            try:
                                print(f"{place['name']} at {place['address']}")
                            except:
                                print(f"{place['name']}")
                        except:
                            print(f"{place['name']}")

                except:
                    pass
                '''
        # Make the API call
        local_food = self.search_places(location, query="authentic food")
        fast_food = self.search_places(location, query="fast food")
        high_dining = self.search_places(location, query="high dining")
        city_tours = self.search_places(location, query="{} tour".format(location))
        museum = self.search_places(location, query="museum")
        nature = self.search_places(location, query="wildlife")
        history = self.search_places(location, query="historical tour")
        hotels = self.search_places(location, query="hotel")
        for place in hotels:
            try:
                print(f"{place['name']} at {place['location']['address']}")
                place = Place(place['name'], place['location']['address'], type="hotel")
                self.itinerary.add_place(place)
                print('added')
                '''

            except KeyError:
                try:
                    print(f"{place['name']} at {place['address']}")
                except:
                    print(f"{place['name']} at {place['location']}")
                     '''
            except:
                print(f"{place['name']} at {place['location']}")

        print(self.itinerary.places)

        # Example: Add a new place to the itinerary
        self.itinerary.create_distance_matrix()
        print("created distance matrix")
        for element in self.itinerary.distance_matrix:
            print(self.itinerary.distance_matrix[element])
        done = False
        while not done:
            done = self.itinerary.execute_step()
        print(f"Optimized Path: {[place.name for place in self.itinerary.final]}")

    def search_places(self, location, query):
        location = urllib.parse.quote(location)
        url = f"https://api.foursquare.com/v3/places/search?query={query}&near={location}"
        headers = {
            "accept": "application/json",
            "Authorization": FOURSQUARE_API_KEY,
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('results', [])
        else:
            print(f"Error fetching places: {response.status_code}")
            return []


if __name__ == "__main__":
    app = TripPlannerUI()
    app.mainloop()
