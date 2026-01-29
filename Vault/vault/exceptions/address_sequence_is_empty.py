class AddressSequenceIsEmpty(Exception):
    def __init__(self, sequence):
        super().__init__(f"Address sequence {sequence.name} is empty")
