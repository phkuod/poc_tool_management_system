import pandas as pd
from datetime import datetime, timedelta

# Create a sample DataFrame
data = {
    'Tool_Number': ['T001', 'T002', 'T003', 'T004'],
    'Tool Column': ['ProjectA', 'ProjectB', 'ProjectA', 'ProjectC'],
    'Customer schedule': [
        datetime.now() + timedelta(days=10),
        datetime.now() + timedelta(days=20),
        datetime.now() + timedelta(days=5),
        datetime.now() + timedelta(days=30)
    ],
    'Responsible User': ['user1@example.com', 'user2@example.com', 'user1@example.com', 'user3@example.com']
}
df = pd.DataFrame(data)

# Create a dummy directory structure
from pathlib import Path
Path("/Target/Path/ProjectA").mkdir(parents=True, exist_ok=True)
Path("/Target/Path/ProjectB").mkdir(parents=True, exist_ok=True)
Path("/Target/Path/ProjectC").mkdir(parents=True, exist_ok=True)

# Create dummy files
Path("/Target/Path/ProjectA/some_file_T001_extra.txt").touch()
Path("/Target/Path/ProjectA/Final_Report_T003_final.pdf").touch()


# Save to Excel
df.to_excel('schedule.xlsx', index=False)
