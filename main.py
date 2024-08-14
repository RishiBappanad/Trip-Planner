import tkinter as tk
from itenerary import Itinerary
from place import Place


class TripPlannerUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Trip Planner")
        self.geometry("400x700")

        # Instance of the Itinerary class
        self.itinerary = Itinerary()

        # Location entry
        tk.Label(self, text="Enter Location:").pack(pady=5)
        self.location_entry = tk.Entry(self)
        self.location_entry.pack(pady=5)

        # Car or no car option
        tk.Label(self, text="Transportation:").pack(pady=5)
        self.car_var = tk.BooleanVar()
        self.car_check = tk.Checkbutton(self, text="Rent a Car", variable=self.car_var)
        self.car_check.pack(pady=5)

        # Hotel budget per night
        tk.Label(self, text="Hotel Budget per Night:").pack(pady=5)
        self.budget_slider = tk.Scale(self, from_=50, to_=1000, orient=tk.HORIZONTAL)
        self.budget_slider.pack(pady=5)

        # Stay duration
        tk.Label(self, text="Stay Duration (days):").pack(pady=5)
        self.duration_slider = tk.Scale(self, from_=1, to_=30, orient=tk.HORIZONTAL)
        self.duration_slider.pack(pady=5)

        # Dining preferences
        tk.Label(self, text="Dining Preferences:").pack(pady=5)
        self.canvas = tk.Canvas(self, width=300, height=50)
        self.canvas.pack(pady=5)

        # Initial positions
        self.pos1 = 100
        self.pos2 = 200

        # Draw the slider
        self.draw_slider()

        self.canvas.bind("<B1-Motion>", self.move_handle)
        self.canvas.bind("<Button-1>", self.move_handle)

        # Tours preferences
        tk.Label(self, text="Tours:").pack(pady=5)
        self.tours_options = tk.Listbox(self, selectmode=tk.MULTIPLE)
        tours = ["City Tour", "Museum Tour", "Nature Tour", "Historical Tour", "Physical Activity"]
        for tour in tours:
            self.tours_options.insert(tk.END, tour)
        self.tours_options.pack(pady=5)

        # Submit button
        self.submit_button = tk.Button(self, text="Submit", command=self.submit)
        self.submit_button.pack(pady=20)

    def draw_slider(self):
        self.canvas.delete("all")

        # Draw the base line
        self.canvas.create_line(50, 25, 250, 25, fill="gray", width=2)

        # Draw the segments
        self.canvas.create_line(50, 25, self.pos1, 25, fill="red", width=6)
        self.canvas.create_line(self.pos1, 25, self.pos2, 25, fill="green", width=6)
        self.canvas.create_line(self.pos2, 25, 250, 25, fill="blue", width=6)

        # Draw the handles
        self.canvas.create_oval(self.pos1 - 5, 20, self.pos1 + 5, 30, fill="black")
        self.canvas.create_oval(self.pos2 - 5, 20, self.pos2 + 5, 30, fill="black")

        # Display percentages
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

        # Example: Add a new place to the itinerary
        new_place = Place(location=(0, 0), type="Hotel")  # Replace with real data from Foursquare API
        self.itinerary.add_place(new_place)
        print(f"Added new place: {new_place.location} of type {new_place.type}")

        # Run itinerary optimization
        self.itinerary.execute_step()
        print(f"Optimized Path: {[place.location for place in self.itinerary.final]}")


if __name__ == "__main__":
    app = TripPlannerUI()
    app.mainloop()
