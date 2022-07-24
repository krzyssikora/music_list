import config
import csv
import sqlite3
import database


def old_records_from_csv(my_file, albums_list):
    with open(my_file, encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        mapping = {"kto":       "artist_name",
                   "co":        "album_title",
                   # "data":    "date_orig",
                   "data":      "date_publ",
                   "ord":       "sort_name",
                   "część":     "part_id",
                   "uwagi":     "notes",
                   "wytwórnia": "publisher",
                   "genre":     "type"
                   }
        if albums_list is None:
            count = 1
        else:
            count = len(albums_list) + 1
        one_of_many = False
        first_of_many_id = None
        for row in reader:
            if count >= 11:
                pass
            new_album = dict()
            albums_list.append(new_album)
            new_album["item_id"] = count
            for key, value in row.items():
                if key == "medium":
                    if value != "":
                        new_album["medium"] = value
                    else:
                        new_album["medium"] = "CD"
                elif key in mapping.keys() and value != "":
                    if key == "część":
                        new_album["part_id"] = int(float(value))
                        if not one_of_many:
                            one_of_many = True
                            first_of_many_id = count
                        new_album["first_part_id"] = first_of_many_id
                    new_key = mapping.get(key, "error")
                    if new_key not in new_album:
                        new_album[new_key] = value
                elif key == "część" and value == "":
                    one_of_many = False
                    first_of_many_id = None
            count += 1
    return albums_list


def old_records_from_csv_classics(my_file, albums_list):
    with open(my_file, encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        mapping = {"kto":           "artist_name",
                   "co":            "album_title",
                   "data nagrania": "date_orig",
                   "data wydania":  "date_publ",
                   "ord":           "sort_name",
                   "część":         "part_id",
                   "uwagi":         "notes",
                   "wytwórnia":     "publisher",
                   "typ":           "type",
                   "genre":         "genre"
                   }
        artist_mapping = {
            "kompozytor":    "artist_name",
            "dyrygent":      "artist_name",
            "orkiestra":     "artist_name",
            "soliści":       "artist_name"
        }
        artists_list = list()

        count = 1303
        one_of_many = False
        first_of_many_id = None
        for row in reader:
            new_album = dict()
            albums_list.append(new_album)
            new_album["item_id"] = count
            for key, value in row.items():
                if key == "medium":
                    if value != "":
                        new_album["medium"] = value
                    else:
                        new_album["medium"] = "CD"
                elif key in mapping.keys() and value != "":
                    if key == "część":
                        new_album["part_id"] = int(float(value))
                        if not one_of_many:
                            one_of_many = True
                            first_of_many_id = count
                        new_album["first_part_id"] = first_of_many_id
                    new_key = mapping.get(key, "error")
                    if new_key not in new_album:
                        new_album[new_key] = value
                elif key == "część" and value == "":
                    one_of_many = False
                    first_of_many_id = None
                elif key == "orkiestra" and value != "":
                    artists_list.append({"artist_type": "band", "artist_name": value})
                elif key in artist_mapping.keys() and value != "":
                    artists_list.append({"artist_type": "person",  "artist_name": value})
            count += 1
    return albums_list, artists_list


def old_database_from_list(my_list, artists=None):
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS albums
    (item_id INTEGER PRIMARY KEY, parts INTEGER, part_id INTEGER, first_part_id INTEGER, 
    artist_type TEXT, artist_name TEXT, artist_surname TEXT, artist_firstname TEXT, artist_role TEXT, 
    sort_name TEXT, album_title TEXT, content TEXT, publisher TEXT, medium TEXT, 
    date_orig TEXT, date_publ TEXT, notes TEXT, type TEXT, genre TEXT)
    ''')
    cur.execute('''CREATE TABLE IF NOT EXISTS artists
    (artist_id INTEGER PRIMARY KEY AUTOINCREMENT, artist_type TEXT, 
    artist_name TEXT, artist_surname TEXT, artist_firstname TEXT, artist_role TEXT)
    ''')
    for record in my_list:
        if "item_id" not in record:
            raise ValueError("item_id missing in the record: ", record)
        else:
            # check if item_id is in the database, add record
            rows_with_id = \
                cur.execute("SELECT COUNT(*) FROM albums WHERE item_id = ?", (record.get("item_id"),)).fetchone()[0]
            if rows_with_id == 0:
                # add record
                placeholder = ", ".join(["?"] * len(record))
                stmt = "INSERT INTO albums ({columns}) VALUES ({values});".format(columns=",".join(record.keys()),
                                                                                  values=placeholder)
                cur.execute(stmt, list(record.values()))
            # add artist
            rows_with_artist = \
                cur.execute("SELECT COUNT(*) FROM artists WHERE artist_name = ?",
                            (record.get("artist_name"),)).fetchone()[0]
            if rows_with_artist == 0:
                # add artist
                cur.execute("INSERT INTO artists (artist_name) VALUES (?)", (record.get("artist_name"),))
            else:
                # more complicated - same artist, new role?, or delete artist_role and pass here
                pass
    for record in artists:
        rows_with_artist = \
            cur.execute("SELECT COUNT(*) FROM artists WHERE artist_name = ?",
                        (record.get("artist_name"),)).fetchone()[0]
        if rows_with_artist == 0:
            # add artist
            cur.execute("INSERT INTO artists (artist_name, artist_type) VALUES (?, ?)",
                        (record.get("artist_name"), record.get("artist_type")))
        else:
            # more complicated - same artist, new role?, or delete artist_role and pass here
            pass
    conn.commit()
    cur.close()


def old_artist_types():
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM artists")
    cur.execute("SELECT * FROM artists")
    lines = cur.fetchall()
    for row in lines:
        if row[1] == 'other':
            artist_types_dict = {1: "person", 2: "band", 3: "other", 0: 'break', "": "leave empty"}
            print(artist_types_dict)
            artist_type = input(row[2] + ": ")
            if artist_type == "":
                continue
            if artist_type == "0":
                break
            artist_id = row[0]
            cur.execute("UPDATE artists SET artist_type = (?) WHERE artist_id = (?)",
                        (artist_types_dict.get(int(artist_type)), artist_id))
    conn.commit()
    cur.close()


def old_get_person_first_last_and_sort_names():
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM artists")
    cur.execute("SELECT * FROM artists")
    lines = cur.fetchall()
    for row in lines:
        if row[1] == 'person':
            artist_id, artist_type, artist_name, artist_surname, artist_firstname, artist_role, sort_name = row
            artist_names = artist_name.split()
            if artist_surname is None or artist_surname == '':
                if len(artist_names) == 2:
                    artist_firstname, artist_surname = artist_names
                elif len(artist_names) == 1:
                    artist_firstname, artist_surname = artist_name, None
                else:
                    artist_firstname, artist_surname = ' '.join(artist_names[:-1]), artist_names[-1]
            if sort_name is None or sort_name == '':
                sort_name = ((artist_surname or '') + ' ' + str(artist_firstname)).strip()
            cur.execute("""
            UPDATE artists SET artist_firstname = (?), 
            artist_surname = (?), sort_name = (?) WHERE artist_id = (?)""",
                        (artist_firstname, artist_surname, sort_name, artist_id))
    conn.commit()
    cur.close()


def old_get_duplicate_artists(ratio=0.85):
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    duplicate_list = list()

    cur.execute("SELECT artist_id, artist_name, artist_role FROM artists")
    lines = cur.fetchall()
    for idx, line in enumerate(lines):
        id1, name1, role1 = line
        duplicates = [line]
        for idx2 in range(idx + 1, len(lines)):
            id2, name2, role2 = lines[idx2]
            if database.similarity_ratio(name1, name2) >= ratio:
                duplicates.append(lines[idx2])
        if len(duplicates) > 1:
            duplicate_list.append(duplicates)
    conn.commit()
    cur.close()
    return duplicate_list


def old_add_main_artist_id_to_albums():
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    cur.execute("""SELECT albums.album_id, albums.artist_name, artists.artist_id FROM albums
    INNER JOIN artists ON albums.artist_name = artists.artist_name""")
    lines = cur.fetchall()
    for line in lines:
        album_id, artist_name, main_artist_id = line
        print(main_artist_id)
        # cur.execute("UPDATE albums SET main_artist_id = (?) WHERE album_id = (?)", (main_artist_id, album_id))
    conn.commit()
    cur.close()


def find_null_main_artist_id_in_albums():
    conn = sqlite3.connect(config.DATABASE)
    cur = conn.cursor()
    cur.execute("""SELECT album_id, artist_name, album_title, main_artist_id FROM albums
    WHERE main_artist_id IS NULL""")
    lines = cur.fetchall()
    for line in lines:
        album_id, artist_name, album_title, main_artist_id = line
        if artist_name is None or artist_name.lower() == 'various':
            cur.execute("UPDATE albums SET main_artist_id = (?) WHERE album_id = (?)",
                        (1413, album_id))  # i.e. 'various'
            continue
        print(line)
        users_main_artist = input('Who is the main artist?')
        cur.execute("SELECT artist_id, artist_name FROM artists WHERE artist_name = (?)", (users_main_artist,))
        artists = cur.fetchall()

        if len(artists) == 0:
            print('   No artist found.')
        elif len(artists) == 1:
            print(artists[0])
            choice = input('Is it the correct artist? (y/n) ')
            if choice in {'y', 'Y'}:
                cur.execute("UPDATE albums SET main_artist_id = (?) WHERE album_id = (?)",
                            (artists[0][0], album_id))
        else:
            for idx, artist in enumerate(artists):
                print(str(idx + 1) + ': ' + '...'.join(map(str, artist)))
                choice = input('Which one is the correct artist?')
                if choice.isdigit():
                    choice = int(choice) - 1
                    if 0 <= choice < len(artists):
                        cur.execute("UPDATE albums SET main_artist_id = (?) WHERE album_id = (?)",
                                    (artists[choice][0], album_id))
    conn.commit()
    cur.close()
    print(len(lines))


if __name__ == '__main__':
    # tmp_artist_types()
    # print(find_similar_artist({'artist_name': 'paton'}, 0.6))
    old_get_person_first_last_and_sort_names()
    pass
