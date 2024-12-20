import tkinter as tk
from tkinter import ttk, messagebox
import tkinter.font as tkfont
import json
import os
import datetime
from utils import load_teams, load_maps


class UTOWPocketCoordinator(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("UTOW Pocket Coordinator")
        self.geometry("600x800")
        self.minsize(600, 800)

        self.custom_font = tkfont.Font(family="Small Fonts", size=10, weight="normal")

        # create styles
        self.style = ttk.Style()
        self.style.configure("TLabel", font=self.custom_font)
        self.style.configure("TButton", font=self.custom_font)
        self.style.configure("TCombobox", font=self.custom_font)
        self.style.configure("TEntry", font=self.custom_font)
        self.style.configure("Header.TLabelframe.Label", foreground="#b54882", font=self.custom_font)

        # load teams + maps
        self.teams = load_teams()
        self.maps = load_maps()

        # find match number
        self.num_teams = len(self.teams)
        self.num_matches = self.num_teams // 2

        # handle bye team
        if self.num_teams % 2 == 1:
            self.bye_team = tk.StringVar()
        else:
            self.bye_team = None

        # define game mode order
        self.game_mode_order = ["control", "hybrid", "flashpoint", "push", "escort", "clash"]
        self.last_week_file = 'last_week_matches.json'
        self.next_week_match_widgets = []

        # define header color
        self.header_color = "#b54882"

        # create ui
        self.create_widgets()

    def create_widgets(self):

        # main window
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # scrollable containers
        container = ttk.Frame(self)
        container.grid(row=0, column=0, sticky="nsew")

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # matches this week frame
        self.matches_frame = ttk.LabelFrame(scrollable_frame, text="Matches This Week", style="Header.TLabelframe")
        self.matches_frame.pack(fill="x", padx=10, pady=10)

        self.match_widgets = []
        self.render_matches()

        # matches next week frame
        self.next_week_frame = ttk.LabelFrame(scrollable_frame, text="Matches Next Week", style="Header.TLabelframe")
        self.next_week_frame.pack(fill="x", padx=10, pady=10)

        self.next_week_match_widgets = []
        self.render_next_week_matches()

        # announcement frame
        announcement_frame = ttk.LabelFrame(scrollable_frame, text="Announcement", style="Header.TLabelframe")
        announcement_frame.pack(fill="x", padx=10, pady=10)

        self.announcement_text = tk.Text(
            announcement_frame, wrap="word", height=10, font=self.custom_font
        )
        self.announcement_text.pack(fill="both", expand=True, padx=5, pady=5)

        # buttons frame
        buttons_frame = ttk.Frame(scrollable_frame)
        buttons_frame.pack(fill="x", padx=10, pady=10)

        generate_btn = ttk.Button(buttons_frame, text="Generate Announcement", command=self.generate_announcement)
        generate_btn.pack(side="left", padx=5)

        copy_btn = ttk.Button(buttons_frame, text="Copy to Clipboard", command=self.copy_to_clipboard)
        copy_btn.pack(side="left", padx=5)

    def render_matches(self):

        # clean widgets
        for widget in self.match_widgets:
            widget["frame"].destroy()
        self.match_widgets.clear()

        for match_num in range(1, self.num_matches + 1):
            frame = ttk.LabelFrame(self.matches_frame, text=f"Match {match_num}", style="Header.TLabelframe")
            frame.pack(fill="x", padx=5, pady=5)

            # teams selection
            ttk.Label(frame, text="Team 1:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            team1_var = tk.StringVar()
            team1_dropdown = ttk.Combobox(
                frame, values=self.teams, textvariable=team1_var, state="readonly", width=25
            )
            team1_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            team1_dropdown.set('')

            ttk.Label(frame, text="Team 2:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
            team2_var = tk.StringVar()
            team2_dropdown = ttk.Combobox(
                frame, values=self.teams, textvariable=team2_var, state="readonly", width=25
            )
            team2_dropdown.grid(row=0, column=3, padx=5, pady=5, sticky="w")
            team2_dropdown.set('')

            # prevent same team selection
            team1_dropdown.bind(
                "<<ComboboxSelected>>",
                lambda event, t2_dropdown=team2_dropdown: self.validate_teams(event, t2_dropdown)
            )
            team2_dropdown.bind(
                "<<ComboboxSelected>>",
                lambda event, t1_dropdown=team1_dropdown: self.validate_teams(event, t1_dropdown)
            )

            # number of games within match
            ttk.Label(frame, text="Number of Games:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            games_control_frame = ttk.Frame(frame)
            games_control_frame.grid(row=1, column=1, padx=5, pady=5, sticky="w")

            decrease_game_btn = ttk.Button(
                games_control_frame, text="-",
                command=lambda m=match_num: self.decrement_game(m)
            )

            decrease_game_btn.pack(side="left")
            game_var = tk.IntVar(value=3)  # default: 3
            game_label = ttk.Label(games_control_frame, textvariable=game_var)
            game_label.pack(side="left", padx=5)

            increase_game_btn = ttk.Button(
                games_control_frame, text="+",
                command=lambda m=match_num: self.increment_game(m)
            )

            increase_game_btn.pack(side="left")

            # store references
            match_info = {
                "frame": frame,
                "team1": team1_var,
                "team2": team2_var,
                "games": game_var,
                "game_widgets": []
            }
            self.match_widgets.append(match_info)

            # maps and winners for each game
            for game_num in range(1, game_var.get() + 1):
                self.create_game_widgets(frame, match_info, game_num)

    def create_game_widgets(self, frame, match_info, game_num):
        ttk.Label(frame, text=f"Game {game_num} Map:").grid(row=2 + game_num, column=0, padx=5, pady=2, sticky="e")
        map_var = tk.StringVar()

        # calculate game mode based on game number
        if 1 <= game_num <= 6:
            game_mode = self.game_mode_order[game_num - 1]
            available_maps = self.maps.get(game_mode, [])
        else:
            available_maps = []

        map_dropdown = ttk.Combobox(
            frame, values=available_maps, textvariable=map_var, state="readonly", width=25
        )

        map_dropdown.grid(row=2 + game_num, column=1, padx=5, pady=2, sticky="w")
        map_dropdown.set('')

        ttk.Label(frame, text="Winner:").grid(row=2 + game_num, column=2, padx=5, pady=2, sticky="e")
        winner_var = tk.StringVar()

        # initialize winner options
        winner_options = ["Draw", match_info["team1"].get(), match_info["team2"].get()]
        winner_dropdown = ttk.Combobox(
            frame, values=winner_options, textvariable=winner_var, state="readonly", width=25
        )
        winner_dropdown.grid(row=2 + game_num, column=3, padx=5, pady=2, sticky="w")
        winner_dropdown.set('')

        # update winner options (when team(s) change)
        match_info["team1"].trace_add("write", lambda *args, m=match_info, g=game_num: self.update_winner_options(m, g))
        match_info["team2"].trace_add("write", lambda *args, m=match_info, g=game_num: self.update_winner_options(m, g))

        game_widget = {
            "map": map_var,
            "winner": winner_var,
            "winner_dropdown": winner_dropdown
        }
        match_info["game_widgets"].append(game_widget)

    def increment_game(self, match_num):

        for widget in self.match_widgets:
            if widget["frame"].cget("text") == f"Match {match_num}":

                if widget["games"].get() < 6:
                    widget["games"].set(widget["games"].get() + 1)
                    new_game_num = widget["games"].get()
                    self.create_game_widgets(widget["frame"], widget, new_game_num)

                else:
                    messagebox.showwarning("Maximum Games", "Cannot have more than 6 games.")

                break

    def decrement_game(self, match_num):

        for widget in self.match_widgets:

            if widget["frame"].cget("text") == f"Match {match_num}":
                if widget["games"].get() > 3:
                    last_game_num = widget["games"].get()

                    # remove last game widget
                    for col in range(4):
                        slaves = widget["frame"].grid_slaves(row=2 + last_game_num, column=col)
                        if slaves:
                            slaves[0].destroy()
                    widget["game_widgets"].pop()
                    widget["games"].set(widget["games"].get() - 1)

                else:
                    messagebox.showwarning("Minimum Games", "Cannot have less than 3 games.")

                break

    def update_winner_options(self, match_info, game_num):

        team1 = match_info["team1"].get()
        team2 = match_info["team2"].get()
        if game_num - 1 < len(match_info["game_widgets"]):
            game_widget = match_info["game_widgets"][game_num - 1]
            game_widget["winner"].set('')
            game_widget["winner_dropdown"]["values"] = ["Draw", team1, team2]

    def validate_teams(self, event, other_dropdown):

        selected_team = event.widget.get()
        other_selected = other_dropdown.get()

        if selected_team == other_selected:
            messagebox.showerror("Invalid Selection", "Both teams in a match must be different.")
            event.widget.set('')

    def generate_announcement(self):
        try:
            last_week_data = []
            for widget in self.match_widgets:
                team1 = widget["team1"].get()
                team2 = widget["team2"].get()

                # ensure teams are different and not blank
                if not team1 or not team2:
                    messagebox.showerror(
                        "Incomplete Selection",
                        f"In {widget['frame'].cget('text')}, both teams must be selected."
                    )
                    return

                if team1 == team2:
                    messagebox.showerror(
                        "Invalid Teams",
                        f"In {widget['frame'].cget('text')}, both teams are the same."
                    )
                    return

                match_entry = {
                    "team1": team1,
                    "team2": team2,
                    "games": [],
                    "overall_winner": ""
                }

                team1_wins = 0
                team2_wins = 0

                for game in widget["game_widgets"]:
                    map_name = game["map"].get()
                    winner = game["winner"].get()

                    # ensure map/winner selected
                    if not map_name or not winner:
                        messagebox.showerror(
                            "Incomplete Selection",
                            f"In {widget['frame'].cget('text')}, all games must have a map and a winner selected."
                        )
                        return

                    match_entry["games"].append({"map": map_name, "winner": winner})

                    if winner == team1:
                        team1_wins += 1

                    elif winner == team2:
                        team2_wins += 1

                if team1_wins > team2_wins:
                    match_entry["overall_winner"] = team1

                elif team2_wins > team1_wins:
                    match_entry["overall_winner"] = team2

                else:
                    match_entry["overall_winner"] = "Draw"

                last_week_data.append(match_entry)

            # generate announcement
            announcement = "@Intramurals\n\n"
            announcement += "once again, we're looking to **stream** some games this week.\n"
            announcement += "please schedule your games asap in #match-chats so we can plan to stream them <3\n\n"
            announcement += "**────────────**\n\n"

            # MATCHES LAST WEEK
            announcement += ":hibiscus: **MATCHES LAST WEEK**\n\n"
            for match in last_week_data:
                team1 = match["team1"]
                team2 = match["team2"]
                winner = match["overall_winner"]
                if winner != "Draw":
                    winner_text = f"{winner} WIN"
                else:
                    winner_text = "DRAW"

                match_line = f":coconut:{team1} vs. :coconut:{team2}: {winner_text}\n"

                for game in match["games"]:
                    map_name = game["map"]
                    game_winner = game["winner"]
                    match_line += f"{map_name}: {game_winner}\n"
                match_line += "\n"
                announcement += match_line

            if self.bye_team and self.bye_team.get():
                announcement += f"**────────────**\n\n"
                announcement += f"**Bye:** {self.bye_team.get()} has a bye this week.\n\n"

            # MATCHES THIS WEEK
            announcement += "**────────────**\n\n"
            announcement += ":palm_tree: **MATCHES __THIS__ WEEK**\n\n"

            for match in self.next_week_match_widgets:
                team1 = match["team1"].get()
                team2 = match["team2"].get()
                datetime_str = match["datetime"].get()
                scheduled = match["scheduled"].get()

                # ensure teams are selected and different
                if not team1 or not team2:
                    messagebox.showerror(
                        "Incomplete Selection",
                        f"In Next Week {match['frame'].cget('text')}, both teams must be selected."
                    )
                    return

                if team1 == team2:
                    messagebox.showerror(
                        "Invalid Teams",
                        f"In Next Week {match['frame'].cget('text')}, both teams are the same."
                    )
                    return

                match_line = f"@{team1} vs. @{team2}"
                if scheduled:
                    match_line += " ✅️"
                match_line += f"\n[{datetime_str}]"

                announcement += f"{match_line}\n\n"

            announcement += "**────────────**\n"

            # display announcement
            self.announcement_text.delete("1.0", tk.END)
            self.announcement_text.insert(tk.END, announcement)

            # save the data
            self.save_last_week_matches(last_week_data)

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def copy_to_clipboard(self):

        announcement = self.announcement_text.get("1.0", tk.END).strip()

        if announcement:
            self.clipboard_clear()
            self.clipboard_append(announcement)
            self.update()
            messagebox.showinfo("Copied", "Copied to clipboard!")

        else:
            messagebox.showwarning("No Content", "There is no announcement to copy.")

    def save_last_week_matches(self, data):
        try:
            with open(self.last_week_file, 'w') as file:
                json.dump(data, file, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save last week's matches: {e}")

    def render_next_week_matches(self):

        # clean widgets
        for widget in self.next_week_match_widgets:
            widget["frame"].destroy()
        self.next_week_match_widgets.clear()

        for match_num in range(1, self.num_matches + 1):
            frame = ttk.LabelFrame(self.next_week_frame, text=f"Match {match_num}", style="Header.TLabelframe")
            frame.pack(fill="x", padx=5, pady=5)

            # teams selection
            ttk.Label(frame, text="Team 1:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            team1_var = tk.StringVar()
            team1_dropdown = ttk.Combobox(
                frame, values=self.teams, textvariable=team1_var, state="readonly", width=25
            )
            team1_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")
            team1_dropdown.set('')

            ttk.Label(frame, text="Team 2:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
            team2_var = tk.StringVar()
            team2_dropdown = ttk.Combobox(
                frame, values=self.teams, textvariable=team2_var, state="readonly", width=25
            )
            team2_dropdown.grid(row=0, column=3, padx=5, pady=5, sticky="w")
            team2_dropdown.set('')

            # prevent same team selection
            team1_dropdown.bind(
                "<<ComboboxSelected>>",
                lambda event, t2_dropdown=team2_dropdown: self.validate_teams(event, t2_dropdown)
            )
            team2_dropdown.bind(
                "<<ComboboxSelected>>",
                lambda event, t1_dropdown=team1_dropdown: self.validate_teams(event, t1_dropdown)
            )

            # date/time entry
            ttk.Label(frame, text="Date/Time:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            datetime_var = tk.StringVar()

            # Set default date/time to upcoming Friday at 8PM EST
            default_datetime = self.get_upcoming_friday()
            datetime_var.set(default_datetime)

            datetime_entry = ttk.Entry(frame, textvariable=datetime_var, width=30)
            datetime_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

            # scheduled checkbox
            scheduled_var = tk.BooleanVar()
            scheduled_check = ttk.Checkbutton(frame, text="Scheduled", variable=scheduled_var)
            scheduled_check.grid(row=1, column=2, padx=5, pady=5, sticky="w")

            # store references
            match_info = {
                "frame": frame,
                "team1": team1_var,
                "team2": team2_var,
                "datetime": datetime_var,
                "scheduled": scheduled_var
            }
            self.next_week_match_widgets.append(match_info)

    def get_upcoming_friday(self):
        today = datetime.date.today()
        days_ahead = 4 - today.weekday()  # friday is weekday 4
        if days_ahead <= 0:
            days_ahead += 7
        next_friday = today + datetime.timedelta(days=days_ahead)
        return next_friday.strftime("%A (%b %d) at 8PM EST")


if __name__ == "__main__":
    app = UTOWPocketCoordinator()
    app.mainloop()
