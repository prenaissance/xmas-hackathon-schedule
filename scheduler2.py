import pandas as pd
import copy
import random

subDF = pd.read_csv("sub.csv")
grupDF = pd.read_csv("grupp.csv")
profDF = pd.read_csv("prof.csv")
cabDF = pd.read_csv("cab.csv")

class Subject:
    def __init__(self, id, unitate_curs, teorie, practica, lab, semester_parity):
        self.id = id
        self.unitate_curs = unitate_curs
        self.teorie = teorie
        self.practica = practica
        self.lab = lab
        self.semester_parity = semester_parity
    def __repr__(self):
        # return f"id - {self.id}, unitate_curs - {self.unitate_curs}, teorie - {self.teorie}, practica - {self.practica}, lab - {self.lab}, parity - {self.semester_parity}"
        return f"{self.id}"

class Group:
    def __init__(self, id, name, language, nr_persons, subject_ids):
        self.id = id
        self.name = name
        self.language = language
        self.nr_persons = int(nr_persons)
        self.subject_ids = []
        for num in subject_ids.split(','):
            try:
                self.subject_ids.append(int(num.strip()))
            except:
                pass
    def __repr__(self):
        # return f"name - {self.name}, lang - {self.language}, nr - {self.nr_persons}, sub_ids - {self.subject_ids}"
        return f"{self.name}"

class Professor:
    def __init__(self, id, name, subject, _type, availability):
        self.id = id
        self.name = name
        self.subject = subject
        self.is_lab = _type == "LAB"
        self.availability = availability
    def __repr__(self):
        # return f"id - {self.id}, name - {self.name}, sub - {self.subject}, type - {self.type}, availability - \n{self.availability}"
        return f"{self.name}"

class Cab:
    def __init__(self, id, is_lab, capacity):
        self.id = id
        self.is_lab = is_lab
        self.capacity = capacity
    def __repr__(self):
        return f"id - {self.id}, lab - {self.is_lab}, cap - {self.capacity}"

list_of_subj = []
list_of_groups = []
list_of_profs = []
list_of_cabs = []

for _, row in subDF.iterrows():
    id = row["id"]
    unitate_curs = row["unitate_curs"]
    teorie = row["teorie"]
    practica = row["practica"]
    lab = row["lab"]
    try:
        semester_parity = int(row["semestru"]) % 2
    except:
        continue
    subj = Subject(id, unitate_curs, teorie, practica, lab, semester_parity)
    list_of_subj.append(subj)


for _, row in grupDF.iterrows():
    id = row["id"]
    name = row["speciality"]
    language = row["language"]
    nr_persoane = row["nr_persoane"]
    subject_ids = row["subject_ids"]
    grup = Group(id, name, language, nr_persoane, subject_ids)
    list_of_groups.append(grup)

for _, row in profDF.iterrows():
    id = row["id"]
    name = row["name"]
    subject = row["subject"]
    _type = row["type"]
    availability = []
    weekdays = ["mon", "tue", "wed", "thu", "fri", "sat"]
    for day in weekdays:
        _temp = []
        for j in range(7):
            availability.append(row[f"{day}_per_{j+1}"])
    prof = Professor(id, name, subject, _type, availability)
    list_of_profs.append(prof)

for _, row in cabDF.iterrows():
    id = row["id "]
    is_lab = row["is_lab_cab"]
    nr_persons = row["nr_persons"]
    cab = Cab(id, is_lab, nr_persons)
    list_of_cabs.append(cab)

class ProfGrupPair:
    def __init__(self, prof, group):
        self.prof = prof
        self.group = group
        self.possibilities = set()
        self.entropy = 0

prof_grup_pairs = []
lab_prof_grup_pairs = []
for prof in list_of_profs:
    for grup in list_of_groups:
        if prof.subject in grup.subject_ids:
            if prof.is_lab:
                lab_prof_grup_pairs.append(ProfGrupPair(prof, grup))
            else:
                prof_grup_pairs.append(ProfGrupPair(prof, grup))

class CabState:
    def __init__(self, cab):
        self.prof = None
        self.groups = []
        self.cab = cab
    def __repr__(self):
        return f"{self.prof}, {self.groups}, {self.cab.id}"

spacetime_states = []
group_sets = []
prof_sets = []

for time_index in range(42):
    _time = []
    for cab in list_of_cabs:
        _time.append(CabState(copy.deepcopy(cab)))
    spacetime_states.append(_time)
    group_sets.append(set())
    prof_sets.append(dict())

def get_free_spacetime(prof, group):
    _list = []
    for time_index, _time in enumerate(spacetime_states):
        if not prof.availability[time_index]:
            continue
        if group.name in group_sets[time_index]:
            continue
        if prof.name in prof_sets[time_index]:
            cab_index = prof_sets[time_index][prof.name]
            if spacetime_states[time_index][cab_index].cab.capacity > group.nr_persons:
                _list.append((time_index, cab_index))
                continue
        for cab_index, cab in enumerate(_time):
            cab_lab = cab.cab.is_lab
            if cab_lab and not prof.is_lab or not cab_lab and prof.is_lab:
                continue
            if cab.prof == None:
                _list.append((time_index, cab_index))
            if cab.prof is prof:
                if cab.cab.capacity > group.nr_persons:
                    _list.append((time_index, cab_index))
                break
    return _list

# could be very much optimized

def reset_possibilities(prof_grup_pairs):
    for pair in prof_grup_pairs:
        prof = pair.prof
        group = pair.group
        spacetime_coords = get_free_spacetime(prof, group)
        pair.possibilities = spacetime_coords
        pair.entropy = len(spacetime_coords)

def end_scheduling():
    df = pd.DataFrame(
        spacetime_states,
        columns = list_of_cabs
    )

    df.to_excel("scheduler2.xlsx")
    exit(0)

def calculate(pairs):

    while prof_grup_pairs:
        min_entropy = float("inf")

        reset_possibilities(prof_grup_pairs)

        entropies = [pair.entropy for pair in prof_grup_pairs]

        impossible = []
        for pair in prof_grup_pairs:
            if pair.entropy < min_entropy:
                min_entropy = pair.entropy

        for imp_track in impossible:
            prof_grup_pairs.remove(imp_track)

        if min_entropy == 0:
            print("Impossible state reached")
            end_scheduling()

        lowest_entropy = []
        for pair in prof_grup_pairs:
            if pair.entropy == min_entropy:
                lowest_entropy.append(pair)

        pair_choice = random.choice(lowest_entropy)
        prof = pair_choice.prof
        group = pair_choice.group
        print("entropy -", min_entropy)
        print(prof, group)
        possibility = random.choice(pair_choice.possibilities)
        time_index, cab_index = possibility
        print(list_of_cabs[cab_index].id, list_of_cabs[cab_index].is_lab)
        group_sets[time_index].add(group.name)
        prof_sets[time_index][prof.name] = cab_index
        spacetime = spacetime_states[time_index][cab_index]
        spacetime.prof = prof
        spacetime.groups.append(group)
        spacetime.cab.capacity -= group.nr_persons
        prof_grup_pairs.remove(pair_choice)

calculate(lab_prof_grup_pairs)
calculate(prof_grup_pairs)

# total = 0
# while prof_grup_pairs:
#     prof, group = prof_grup_pairs.pop()
#     spacetime_coords = get_free_spacetime(prof, group)
#     # if spacetime_coords:
#     #     total += 1
#     # time_index, cab_index = random.choice(spacetime_coords)
#     try:
#         time_index, cab_index = spacetime_coords[0]
#         total += 1
#     except:
#         print(spacetime_states)
#     group_sets[time_index].add(group.name)
#     prof_sets[time_index][prof.name] = cab_index
#     spacetime = spacetime_states[time_index][cab_index]
#     spacetime.prof = prof
#     spacetime.groups.append(group)

# for i in group_sets:
#     print(i)

df = pd.DataFrame(
    spacetime_states,
    columns = list_of_cabs
)

df.to_excel("scheduler2.xlsx")
