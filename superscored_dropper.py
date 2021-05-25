import requests
import sys
import pandas
import re

pandas.options.mode.chained_assignment = None

tournament: str = ""
try:
    tournament: str = sys.argv[1].split("/")[-1]
except IndexError:
    print("No tournament (e.g. 2019-06-01_nationals_c) provided!")
    exit(1)
r = requests.get(f"https://duosmium.org/results/{tournament}")
p = pandas.read_html(r.text)
table = p[0]
events = table.columns[5:-1]
trials = [e for e in events if "  T" in e or "  Td" in e]
events = [e for e in events if e not in trials]
full = ["School", "Rank", "Score"] + events + trials + ["Team Penalties"]
mins = {}
for idx in table.index:
    school_list = table["Team"][idx].split("  ")
    school = school_list[0]
    if re.search(r"[A-Z][a-z]", school_list[-1]):
        state = school_list[-2]
    else:
        state = school_list[-1]
    if f"{school} ({state})" not in mins.keys():
        mins[f"{school} ({state})"] = {}
    for evt in events + trials + ["Team Penalties"]:
        if evt not in mins[f"{school} ({state})"].keys():
            mins[f"{school} ({state})"][evt] = table[evt][idx]
        else:
            mins[f"{school} ({state})"][evt] = min(
                table[evt][idx], mins[f"{school} ({state})"][evt]
            )
input_list = [
    [school, "0", "0"]
    + [str(mins[school][evt]).replace("*", "") for evt in events]
    + [str(mins[school][evt]).replace("*", "") for evt in trials]
    + [str(mins[school]["Team Penalties"])]
    for school in mins
]
df = pandas.DataFrame(input_list, columns=full)
for idx in df.index:

    def calculate_score():
        counted = [int(df[evt][idx].replace("*", "")) for evt in events]
        score = sum(counted)
        return score

    df["Score"][idx] = str(calculate_score())
df = df.astype({"Score": int})
df.sort_values(by="Score", inplace=True)
df_dropped = pandas.DataFrame(columns=["School"] + [f"Drop {i}" for i in range(len(events))])
for idx in df.index:
    input_two = [df["School"][idx]]
    for col in df_dropped.columns[1:]:
        num_to_drop = int(col.split(" ")[-1])
        counted = [int(df[evt][idx].replace("*", "")) for evt in events]
        if num_to_drop == 0:
            input_two.append(sum(counted))
        else:
            input_two.append(sum(sorted(counted)[:-(num_to_drop)]))
    df_dropped.loc[len(df_dropped.index)] = input_two

with open(f"{tournament}_superscored_dropped.csv", "w") as fil:
    df_dropped.to_csv(fil, index=False)
