combined_routine = {
    "Sunday": [
        {"time": "6:55 - 8:35", "subject": "OOP", "type": "l"},
        {"time": "8:35 - 10:15", "subject": "DL", "type": "l"},
        {"time": "10:15 - 11:05", "subject": "C", "type": "l"},
        {"time": "11:05 - 11:55", "subject": "BREAK"},
        {
            "time": "11:55 - 14:25",
            "subject": {
                "C": "DL",
                "D": "OOP"
            },
            "type": {
                "C": "p",
                "D": "p"
            }
        }
    ],
    "Monday": [
        {"time": "6:55 - 7:45", "subject": "C", "type": "l"},
        {
            "time": "7:45 - 10:15",
            "subject": {
                "C": "OOP",
                "D": "DL"
            },
            "type": {
                "C": "p",
                "D": "p"
            }
        },
        {"time": "10:15 - 11:05", "subject": "BREAK"},
        {"time": "11:05 - 12:45", "subject": "OOP", "type": "l"}
    ],
    "Tuesday": [
        {"time": "6:55 - 8:35", "subject": "ECM", "type": "l"},
        {"time": "8:35 - 9:25", "subject": "BREAK"},
        {"time": "9:25 - 11:05", "subject": "EDC", "type": "l"},
        {
            "time": "11:05 - 13:35",
            "subject": {
                "C": "BREAK",
                "D": "EDC"
            },
            "type": {
                "C": None,
                "D": "p"
            }
        },
        {"time": "13:35 - 15:15", "subject": "DL", "type": "l"},
        {"time": "15:15 - 16:15", "subject": "Chemistry", "type": "l"},
        {
            "time": "16:16 - 17:15",
            "subject": {
                "C": "OOP",
                "D": "EDC"
            },
            "type": {
                "C": "p",
                "D": "p"
            }
        }
    ],
    "Wednesday": [
        {"time": "7:45 - 8:35", "subject": "M", "type": "l"},
        {"time": "8:45 - 9:25", "subject": "BREAK"},
        {"time": "9:25 - 10:15", "subject": "C", "type": "l"},
        {"time": "10:15 - 11:55", "subject": "EDC", "type": "l"},
        {
            "time": "11:55 - 14:25",
            "subject": {
                "C": "EDC",
                "D": "BREAK"
            },
            "type": {
                "C": "p",
                "D": None
            }
        }
    ],
    "Thursday": [

    ],
    "Friday": [

    ]
}

subject_map = {
    "OOP": "Object Oriented Programming",
    "DL": "Digital Logic",
    "C": "Chemistry",
    "ECM": "Electrical Circuits and Machines",
    "EDC": "Electronic Device and Circuits",
    "M": "Mathematics II",
    "BREAK": "Break Time"
}

type_map = {
    "l": "Lecture",
    "p": "Practical"
}
