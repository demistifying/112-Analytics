def main():
    import pandas as pd
    from datetime import datetime
    import os

    ALLOC_FILE = "data/allocations.xlsx"

    def initialize_allocations():
        if not os.path.exists(ALLOC_FILE):
            df = pd.DataFrame(columns=[
                "timestamp", "officer", "rank", "jurisdiction", 
                "resource_type", "quantity", "shift", "remarks"
            ])
            df.to_excel(ALLOC_FILE, index=False)

    def load_allocations():
        return pd.read_excel(ALLOC_FILE)

    def add_allocation(officer, rank, jurisdiction, resource_type, quantity, shift, remarks=""):
        df = load_allocations()
        new_entry = {
            "timestamp": datetime.now(),
            "officer": officer,
            "rank": rank,
            "jurisdiction": jurisdiction,
            "resource_type": resource_type,
            "quantity": quantity,
            "shift": shift,
            "remarks": remarks
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        df.to_excel(ALLOC_FILE, index=False)
        return new_entry
    pass