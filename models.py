class Player:
    def __init__(self, number, counter_count):
        self.name = f"Player {number}"
        self.values = ["0"] * counter_count
        self.group = "None"
